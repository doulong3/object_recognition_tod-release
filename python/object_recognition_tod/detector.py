#!/usr/bin/env python
"""
Module defining the TOD detector to find objects in a scene
"""

from ecto_opencv import features2d, highgui, imgproc, calib
from feature_descriptor import FeatureDescriptor
from object_recognition_core.boost.interface import DbModels
from object_recognition_core.db.object_db import ObjectDb
from object_recognition_core.pipelines.detection import DetectionPipeline
from object_recognition_core.utils import json_helper
from object_recognition_tod import ecto_detection
import ecto

try:
    import ecto_ros.ector_ros
    import ecto_ros.ecto_sensor_msgs as ecto_sensor_msgs
    ECTO_ROS_FOUND = True
except ImportError:
    ECTO_ROS_FOUND = False

class TodDetector(ecto.BlackBox):
    feature_descriptor = FeatureDescriptor
    descriptor_matcher = ecto_detection.DescriptorMatcher
    guess_generator = ecto_detection.GuessGenerator
    passthrough = ecto.PassthroughN
    if ECTO_ROS_FOUND:
        message_cvt = ecto_ros.ector_ros.Mat2Image

    def __init__(self, submethod, parameters, model_documents, object_db, visualize=False, **kwargs):
        self._submethod = submethod
        self._parameters = parameters
        self._model_documents = model_documents
        self._object_db = object_db

        self._visualize = visualize

        ecto.BlackBox.__init__(self, **kwargs)

    def declare_params(self, p):
        if ECTO_ROS_FOUND:
            p.forward('rgb_frame_id', cell_name='message_cvt', cell_key='frame_id')
        #p.forward('model_documents', cell_name='descriptor_matcher', cell_key='model_documents')

    def declare_io(self, _p, i, o):
        self.passthrough = ecto.PassthroughN(items=dict(image='An image',
                                                   K='The camera matrix'
                                                   )
                                        )
        i.forward(['image', 'K'], cell_name='passthrough', cell_key=['image', 'K'])
        i.forward('mask', cell_name='feature_descriptor', cell_key='mask')
        i.forward('points3d', cell_name='guess_generator', cell_key='points3d')

        o.forward('pose_results', cell_name='guess_generator', cell_key='pose_results')
        o.forward('keypoints', cell_name='feature_descriptor', cell_key='keypoints')

    def configure(self, p, _i, _o):
        feature_params = self._parameters.get("feature", False)
        if not feature_params:
            raise RuntimeError("You must supply feature_descriptor parameters for TOD.")
        # merge it with the subtype
        feature_descriptor_params = { 'feature': feature_params, 'descriptor': self._parameters.get('descriptor', {}) }
        from object_recognition_tod import merge_dict
        feature_descriptor_params = merge_dict(feature_descriptor_params, self._submethod)

        self.feature_descriptor = FeatureDescriptor(json_params=json_helper.dict_to_cpp_json_str(feature_descriptor_params))
        self.descriptor_matcher = ecto_detection.DescriptorMatcher("Matcher",
                                search_json_params=json_helper.dict_to_cpp_json_str(self._parameters['search']),
                                model_documents=self._model_documents)
        if ECTO_ROS_FOUND:
            self.message_cvt = ecto_ros.Mat2Image()

        guess_params = self._parameters['guess'].copy()
        guess_params['visualize'] = self._visualize
        guess_params['db'] = self._object_db

        self.guess_generator = ecto_detection.GuessGenerator("Guess Gen", **guess_params)

    def connections(self):
        # make sure the inputs reach the right cells
        connections = [self.passthrough['image'] >> self.feature_descriptor['image'],
                       self.passthrough['image'] >> self.guess_generator['image'], ]

        connections += [ self.descriptor_matcher['spans'] >> self.guess_generator['spans'],
                       self.descriptor_matcher['object_ids'] >> self.guess_generator['object_ids'] ]

        connections += [ self.feature_descriptor['keypoints'] >> self.guess_generator['keypoints'],
                self.feature_descriptor['descriptors'] >> self.descriptor_matcher['descriptors'],
                self.descriptor_matcher['matches', 'matches_3d'] >> self.guess_generator['matches', 'matches_3d'] ]

        cvt_color = imgproc.cvtColor(flag=imgproc.RGB2GRAY)

        if self._visualize or ECTO_ROS_FOUND:
            draw_keypoints = features2d.DrawKeypoints()
            connections += [ self.passthrough['image'] >> cvt_color[:],
                           cvt_color[:] >> draw_keypoints['image'],
                           self.feature_descriptor['keypoints'] >> draw_keypoints['keypoints']
                           ]

        if self._visualize:
            # visualize the found keypoints
            image_view = highgui.imshow(name="RGB")
            keypoints_view = highgui.imshow(name="Keypoints")


            connections += [ self.passthrough['image'] >> image_view['image'],
                           draw_keypoints['image'] >> keypoints_view['image']
                           ]

            pose_view = highgui.imshow(name="Pose")
            pose_drawer = calib.PosesDrawer()

            # draw the poses
            connections += [ self.passthrough['image', 'K'] >> pose_drawer['image', 'K'],
                              self.guess_generator['Rs', 'Ts'] >> pose_drawer['Rs', 'Ts'],
                              pose_drawer['output'] >> pose_view['image'] ]

        if ECTO_ROS_FOUND:
            ImagePub = ecto_sensor_msgs.Publisher_Image
            pub_features = ImagePub("Features Pub", topic_name='features')
            connections += [ draw_keypoints['image'] >> self.message_cvt[:],
                           self.message_cvt[:] >> pub_features[:] ]

        return connections

########################################################################################################################

class TodDetectionPipeline(DetectionPipeline):
    @classmethod
    def type_name(cls):
        return 'TOD'

    @classmethod
    def detector(self, *args, **kwargs):
        visualize = kwargs.pop('visualize', False)
        submethod = kwargs.pop('submethod')
        parameters = kwargs.pop('parameters')
        object_ids = parameters['object_ids']
        object_db = ObjectDb(parameters['db'])
        model_documents = DbModels(object_db, object_ids, self.type_name(), json_helper.dict_to_cpp_json_str(submethod))
        return TodDetector(submethod, parameters, model_documents, object_db, visualize, **kwargs)
