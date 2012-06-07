/*
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2009, Willow Garage, Inc.
 *  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following
 *     disclaimer in the documentation and/or other materials provided
 *     with the distribution.
 *   * Neither the name of Willow Garage, Inc. nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 *  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 *  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 *  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 *
 */

#ifndef GUESS_GENERATOR_H_
#define GUESS_GENERATOR_H_

#include <vector>

#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

#include <object_recognition_core/db/db.h>
#include "maximum_clique.h"

namespace tod
{
  class AdjacencyRansac
  {
  public:
    AdjacencyRansac()
    {
      query_points_ = boost::shared_ptr < pcl::PointCloud<pcl::PointXYZ> > (new pcl::PointCloud<pcl::PointXYZ>());
      training_points_ = boost::shared_ptr < pcl::PointCloud<pcl::PointXYZ> > (new pcl::PointCloud<pcl::PointXYZ>());
    }

    void
    clear_adjacency();

    void
    FillAdjacency(const std::vector<cv::KeyPoint> & keypoints, float object_span, float sensor_error);

    void
    AddPoints(const cv::Point3f &training_point, const cv::Point3f & query_point, unsigned int query_index);

    void
    InvalidateIndices(std::vector<unsigned int> &indices);

    void
    InvalidateQueryIndices(std::vector<unsigned int> &query_indices);

    unsigned int
    n_points() const
    {
      return query_indices_.size();
    }

    inline const std::vector<unsigned int> &
    query_indices() const
    {
      return query_indices_;
    }

    inline unsigned int
    query_indices(unsigned int index) const
    {
      return query_indices_[index];
    }

    const std::vector<int>
    valid_indices() const
    {
      std::vector<int> valid_indices(valid_indices_.size());
      for (unsigned int i = 0; i < valid_indices_.size(); ++i)
        valid_indices[i] = valid_indices_[i];

      return valid_indices;
    }

    Eigen::VectorXf
    Ransac(float sensor_error, unsigned int n_ransac_iterations, std::vector<int>& inliers);

    object_recognition_core::db::ObjectId object_id_;
    size_t object_index_;
    tod::maximum_clique::Graph graph_;
    /** matrix indicating whether two points are close enough physically */
    maximum_clique::AdjacencyMatrix physical_adjacency_;
    /** matrix indicating whether two points can be drawn in a RANSAC sample (belong to physical_adjacency but are not
     * too close) */
    maximum_clique::AdjacencyMatrix sample_adjacency_;

  private:
    inline pcl::PointCloud<pcl::PointXYZ>::Ptr
    training_points() const
    {
      return training_points_;
    }
    inline pcl::PointXYZ &
    training_points(unsigned int index) const
    {
      return training_points_->points[index];
    }

    inline pcl::PointCloud<pcl::PointXYZ>::Ptr
    query_points() const
    {
      return query_points_;
    }
    inline pcl::PointXYZ &
    query_points(unsigned int index) const
    {
      return query_points_->points[index];
    }

    pcl::PointCloud<pcl::PointXYZ>::Ptr query_points_;
    pcl::PointCloud<pcl::PointXYZ>::Ptr training_points_;
    std::vector<unsigned int> query_indices_;
    /** The list of indices that are actually valid in the current data structures */
    std::vector<unsigned int> valid_indices_;
  };

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

  typedef std::map<size_t, AdjacencyRansac> OpenCVIdToObjectPoints;

  void
  ClusterPerObject(const std::vector<cv::KeyPoint> & keypoints, const cv::Mat &point_cloud,
                   const std::vector<std::vector<cv::DMatch> > & matches, const std::vector<cv::Mat> & matches_3d,
                   OpenCVIdToObjectPoints &object_points);

  void
  DrawClustersPerObject(const std::vector<cv::KeyPoint> & keypoints, const std::vector<cv::Scalar> & colors,
                        const cv::Mat & initial_image, const OpenCVIdToObjectPoints &object_points);

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
}

#endif /* GUESS_GENERATOR_H_ */
