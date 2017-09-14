# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

import imagenet_main
import resnet_model

tf.logging.set_verbosity(tf.logging.ERROR)

_LABEL_CLASSES = 1001


class BaseTest(tf.test.TestCase):
  def tensor_shapes_helper(self, resnet_size):
    """Checks the tensor shapes after each phase of the ResNet model."""
    graph = tf.Graph()

    with graph.as_default():
      model = resnet_model.resnet_v2(resnet_size, 456)
      inputs = tf.random_uniform([1, 224, 224, 3])
      output = model(inputs, is_training=True)

      initial_conv = graph.get_tensor_by_name('initial_conv:0')
      max_pool = graph.get_tensor_by_name('initial_max_pool:0')
      block_layer1 = graph.get_tensor_by_name('block_layer1:0')
      block_layer2 = graph.get_tensor_by_name('block_layer2:0')
      block_layer3 = graph.get_tensor_by_name('block_layer3:0')
      block_layer4 = graph.get_tensor_by_name('block_layer4:0')
      avg_pool = graph.get_tensor_by_name('final_avg_pool:0')
      dense = graph.get_tensor_by_name('final_dense:0')

      self.assertAllEqual(initial_conv.shape, (1, 64, 112, 112))
      self.assertAllEqual(max_pool.shape, (1, 64, 56, 56))

      # The number of channels after each block depends on whether we're
      # using the building_block or the bottleneck_block.
      if resnet_size < 50:
        self.assertAllEqual(block_layer1.shape, (1, 64, 56, 56))
        self.assertAllEqual(block_layer2.shape, (1, 128, 28, 28))
        self.assertAllEqual(block_layer3.shape, (1, 256, 14, 14))
        self.assertAllEqual(block_layer4.shape, (1, 512, 7, 7))
        self.assertAllEqual(avg_pool.shape, (1, 512, 1, 1))
      else:
        self.assertAllEqual(block_layer1.shape, (1, 256, 56, 56))
        self.assertAllEqual(block_layer2.shape, (1, 512, 28, 28))
        self.assertAllEqual(block_layer3.shape, (1, 1024, 14, 14))
        self.assertAllEqual(block_layer4.shape, (1, 2048, 7, 7))
        self.assertAllEqual(avg_pool.shape, (1, 2048, 1, 1))

      self.assertAllEqual(dense.shape, (1, 456))
      self.assertAllEqual(output.shape, (1, 456))

  def test_tensor_shapes_resnet_18(self):
    self.tensor_shapes_helper(18)

  def test_tensor_shapes_resnet_34(self):
    self.tensor_shapes_helper(34)

  def test_tensor_shapes_resnet_50(self):
    self.tensor_shapes_helper(50)

  def test_tensor_shapes_resnet_101(self):
    self.tensor_shapes_helper(101)

  def test_tensor_shapes_resnet_152(self):
    self.tensor_shapes_helper(152)

  def test_tensor_shapes_resnet_200(self):
    self.tensor_shapes_helper(200)

  def input_fn(self):
    """Provides random features and labels."""
    features = tf.random_uniform([FLAGS.train_batch_size, 224, 224, 3])
    labels = tf.one_hot(
        tf.random_uniform(
            [FLAGS.train_batch_size], maxval=_LABEL_CLASSES - 1,
            dtype=tf.int32),
        _LABEL_CLASSES)

    return features, labels

  def resnet_model_fn_helper(self, mode):
    """Tests that the EstimatorSpec is given the appropriate arguments."""
    tf.train.create_global_step()

    features, labels = self.input_fn()
    spec = imagenet_main.resnet_model_fn(features, labels, mode)

    predictions = spec.predictions
    self.assertAllEqual(predictions['probabilities'].shape,
                        (FLAGS.train_batch_size, _LABEL_CLASSES))
    self.assertEqual(predictions['probabilities'].dtype, tf.float32)
    self.assertAllEqual(predictions['classes'].shape, (FLAGS.train_batch_size,))
    self.assertEqual(predictions['classes'].dtype, tf.int64)

    if mode != tf.estimator.ModeKeys.PREDICT:
      loss = spec.loss
      self.assertAllEqual(loss.shape, ())
      self.assertEqual(loss.dtype, tf.float32)

    if mode == tf.estimator.ModeKeys.EVAL:
      eval_metric_ops = spec.eval_metric_ops
      self.assertAllEqual(eval_metric_ops['accuracy'][0].shape, ())
      self.assertAllEqual(eval_metric_ops['accuracy'][1].shape, ())
      self.assertEqual(eval_metric_ops['accuracy'][0].dtype, tf.float32)
      self.assertEqual(eval_metric_ops['accuracy'][1].dtype, tf.float32)

  def test_resnet_model_fn_train_mode(self):
    self.resnet_model_fn_helper(tf.estimator.ModeKeys.TRAIN)

  def test_resnet_model_fn_eval_mode(self):
    self.resnet_model_fn_helper(tf.estimator.ModeKeys.EVAL)

  def test_resnet_model_fn_predict_mode(self):
    self.resnet_model_fn_helper(tf.estimator.ModeKeys.PREDICT)


if __name__ == '__main__':
  FLAGS = imagenet_main.FLAGS
  tf.test.main()
