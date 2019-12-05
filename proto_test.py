# Copyright (c) 2019 The Pybind Development Team. All rights reserved.
#
# All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.
"""Tests for protobuf casters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from google3.testing.pybase import googletest
from google3.testing.pybase import parameterized
from pybind11_protobuf import proto
from pybind11_protobuf import proto_example
from pybind11_protobuf import test_pb2


class ProtoTest(parameterized.TestCase):

  def test_return_wrapped_message(self):
    message = proto_example.make_int_message()
    self.assertEqual(message.DESCRIPTOR.full_name, 'pybind11.test.IntMessage')

  def test_is_wrapped_c_proto(self):
    self.assertTrue(proto.is_wrapped_c_proto(proto_example.make_int_message()))
    self.assertFalse(proto.is_wrapped_c_proto('not a proto'))
    self.assertFalse(proto.is_wrapped_c_proto(5))
    self.assertFalse(proto.is_wrapped_c_proto(test_pb2.IntMessage()))

  @parameterized.named_parameters(
      ('name', 'pybind11.test.IntMessage'),
      ('native_proto', test_pb2.IntMessage()),
      ('native_proto_type', test_pb2.IntMessage),
      ('wrapped_proto', proto_example.make_int_message()))
  def test_make_wrapped_c_proto_from(self, type_in):
    message = proto.make_wrapped_c_proto(type_in)
    self.assertTrue(proto.is_wrapped_c_proto(message))

  def test_access_wrapped_message_singluar_fields(self):
    message = proto_example.make_test_message()
    message.string_value = 'test'
    message.int_value = 5
    message.int_message.value = 6
    self.assertEqual(message.string_value, 'test')
    self.assertEqual(message.int_value, 5)
    self.assertEqual(message.int_message.value, 6)

  def test_access_wrapped_message_repeated_int_value(self):
    message = proto_example.make_test_message()
    message.repeated_int_value.append(6)
    message.repeated_int_value.append(7)

    self.assertLen(message.repeated_int_value, 2)
    self.assertEqual(message.repeated_int_value[0], 6)
    self.assertEqual(message.repeated_int_value[1], 7)
    for value, expected in zip(message.repeated_int_value, [6, 7]):
      self.assertEqual(value, expected)

    self.assertEqual(str(message.repeated_int_value), '[6, 7]')

    message.repeated_int_value[0] = 8
    self.assertSequenceEqual(message.repeated_int_value, [8, 7])

    message.repeated_int_value.insert(1, 2)
    self.assertSequenceEqual(message.repeated_int_value, [8, 2, 7])

    del message.repeated_int_value[1]
    self.assertSequenceEqual(message.repeated_int_value, [8, 7])

    message.repeated_int_value.extend([6, 5])
    self.assertSequenceEqual(message.repeated_int_value, [8, 7, 6, 5])

    message.repeated_int_value[1] = 5
    self.assertSequenceEqual(message.repeated_int_value, [8, 5, 6, 5])

    message.repeated_int_value.clear()
    self.assertEmpty(message.repeated_int_value)

    self.assertRaises(TypeError, message.repeated_int_value.append,
                      'invalid value')

  def test_access_wrapped_message_repeated_int_message(self):
    message = proto_example.make_test_message()
    sub_msg = proto_example.make_int_message()
    sub_msg.value = 6
    message.repeated_int_message.append(sub_msg)
    # Append/Extend/Set should work from native or wrapped messages.
    sub_msg = test_pb2.IntMessage()
    sub_msg.value = 7
    message.repeated_int_message.append(sub_msg)

    def check_values(values):
      for msg, expected in zip(message.repeated_int_message, values):
        self.assertEqual(msg.value, expected)

    self.assertLen(message.repeated_int_message, 2)
    self.assertEqual(message.repeated_int_message[0].value, 6)
    self.assertEqual(message.repeated_int_message[1].value, 7)
    check_values([6, 7])

    self.assertEqual(str(message.repeated_int_message), '[value: 6, value: 7]')

    message.repeated_int_message[0].value = 8
    check_values([8, 7])

    sub_msg.value = 2
    message.repeated_int_message.insert(1, sub_msg)
    check_values([8, 2, 7])

    message.repeated_int_message.extend([sub_msg, sub_msg])
    check_values([8, 2, 7, 2, 2])

    # TODO(b/145687965): Get element removal to work.
    with self.assertRaises(RuntimeError):
      del message.repeated_int_message[1]

    message.repeated_int_message.clear()
    self.assertEmpty(message.repeated_int_message)

    self.assertRaises(RuntimeError, message.repeated_int_message.append,
                      'invalid value')
    self.assertRaises(RuntimeError, message.repeated_int_message.append,
                      test_pb2.TestMessage())

  def test_access_wrapped_message_map_string_int(self):
    message = proto_example.make_test_message()

    message.string_int_map['k1'] = 5
    message.string_int_map['k2'] = 6
    self.assertLen(message.string_int_map, 2)
    self.assertEqual(message.string_int_map['k1'], 5)
    self.assertEqual(message.string_int_map['k2'], 6)
    self.assertIn('k1', message.string_int_map)
    self.assertIn('k2', message.string_int_map)
    self.assertNotIn('k3', message.string_int_map)

    native = test_pb2.TestMessage()
    native.string_int_map['k1'] = 5
    native.string_int_map['k2'] = 6
    self.assertEqual(str(message.string_int_map), str(native.string_int_map))

    message.string_int_map.clear()
    self.assertEmpty(message.string_int_map)

    with self.assertRaises(TypeError):
      message.string_int_map[5] = 5  # invalid key.
    with self.assertRaises(TypeError):
      message.string_int_map['k'] = 'foo'  # invalid value.

  def test_access_wrapped_message_map_int_message(self):
    message = proto_example.make_test_message()

    message.int_message_map[5].value = 2
    message.int_message_map[6].value = 3
    self.assertLen(message.int_message_map, 2)
    self.assertEqual(message.int_message_map[5].value, 2)
    self.assertEqual(message.int_message_map[6].value, 3)
    self.assertIn(5, message.int_message_map)
    self.assertIn(6, message.int_message_map)
    self.assertNotIn(7, message.int_message_map)

    self.assertEqual(str(message.int_message_map), '{5: value: 2, 6: value: 3}')

    message.int_message_map.clear()
    self.assertEmpty(message.int_message_map)

    with self.assertRaises(TypeError):
      message.int_message_map['foo'].value = 5  # invalid key.

  def test_access_wrapped_message_enum(self):
    message = proto_example.make_test_message()

    self.assertEqual(message.enum_value, 0)

    message.enum_value = 1
    self.assertEqual(message.enum_value, test_pb2.TestMessage.ONE)

    message.enum_value = test_pb2.TestMessage.TWO
    self.assertEqual(message.enum_value, 2)

  def test_access_wrapped_message_repeated_enum(self):
    message = proto_example.make_test_message()

    message.repeated_enum_value.append(test_pb2.TestMessage.TWO)
    message.repeated_enum_value.append(test_pb2.TestMessage.ONE)
    self.assertLen(message.repeated_enum_value, 2)
    self.assertEqual(message.repeated_enum_value[0], 2)
    self.assertEqual(message.repeated_enum_value[1], 1)
    self.assertEqual(str(message.repeated_enum_value), '[TWO, ONE]')

  def test_access_nonexistent_field(self):
    message = proto_example.make_test_message()
    with self.assertRaises(AttributeError):
      _ = message.invalid_field  # get
    with self.assertRaises(AttributeError):
      message.invalid_field = 5  # set

  def test_invalid_field_assignment(self):
    # Message, repeated, and map fields cannot be set via assignment.
    message = proto_example.make_test_message()
    with self.assertRaises(AttributeError):
      message.int_message = test_pb2.IntMessage()
    with self.assertRaises(AttributeError):
      message.repeated_int_value = []
    with self.assertRaises(AttributeError):
      message.repeated_int_message = []
    with self.assertRaises(AttributeError):
      message.repeated_enum_value = []
    with self.assertRaises(AttributeError):
      message.string_int_map = {}
    with self.assertRaises(AttributeError):
      message.int_message_map = {}

  def test_pass_wrapped_proto(self):
    message = proto_example.make_int_message()
    message.value = 5
    self.assertTrue(proto_example.check_int_message(message, 5))

  def test_pass_wrapped_proto_wrong_type(self):
    message = proto_example.make_test_message()
    self.assertRaises(TypeError, proto_example.check_int_message, message, 5)

  def test_pass_native_proto(self):
    message = test_pb2.IntMessage()
    message.value = 5
    self.assertTrue(proto_example.check_int_message(message, 5))

  def test_pass_native_proto_wrong_type(self):
    message = test_pb2.TestMessage()
    self.assertRaises(TypeError, proto_example.check_int_message, message, 5)

  def test_pass_not_a_proto(self):
    self.assertRaises(TypeError, proto_example.check_int_message, 'not_a_proto',
                      5)

  def test_mutate_wrapped_proto(self):
    message = proto_example.make_int_message()
    proto_example.mutate_int_message(5, message)
    self.assertEqual(message.value, 5)

  def test_mutate_native_proto(self):
    # This is not allowed (enforce by `.noconvert()` on the argument binding).
    message = test_pb2.TestMessage()
    self.assertRaises(TypeError, proto_example.mutate_int_message, 5, message)

  def test_pass_generic_wrapped_proto(self):
    message = proto_example.make_test_message()
    self.assertTrue(
        proto_example.check_abstract_message(message,
                                             message.DESCRIPTOR.full_name))

  def test_pass_generic_native_proto(self):
    message = test_pb2.TestMessage()
    self.assertTrue(
        proto_example.check_abstract_message(message,
                                             message.DESCRIPTOR.full_name))

  def test_make_any_from_wrapped_proto(self):
    message = proto_example.make_test_message()
    message.int_value = 5
    any_proto = proto_example.make_any_message(message)
    self.assertEqual(any_proto.type_url,
                     'type.googleapis.com/pybind11.test.TestMessage')
    self.assertEqual(any_proto.value, b'\x10\x05')

  def test_make_any_from_native_proto(self):
    message = test_pb2.TestMessage()
    message.int_value = 5
    any_proto = proto_example.make_any_message(message)
    self.assertEqual(any_proto.type_url,
                     'type.googleapis.com/pybind11.test.TestMessage')
    self.assertEqual(any_proto.value, b'\x10\x05')

  @parameterized.named_parameters(
      ('int_message_ref', proto_example.get_int_message_ref),
      ('int_message_raw_ptr', proto_example.get_int_message_raw_ptr),
      ('abstract_message_ref', proto_example.get_abstract_message_ref),
      ('abstract_message_raw_ptr', proto_example.get_abstract_message_raw_ptr))
  def test_static_value(self, get_message_function):
    message_1 = get_message_function()
    message_1.value = 5
    self.assertEqual(message_1.value, 5)
    message_2 = get_message_function()
    message_2.value = 6
    self.assertEqual(message_2.value, 6)
    # get_message_function always returns a reference to the same static
    # object, so message_1 and message_2 should always be equal.
    self.assertEqual(message_1.value, message_2.value)
    # test passing the message as a concrete type.
    self.assertTrue(proto_example.check_int_message(message_1, 6))
    # test passing the message as an abstract type.
    self.assertTrue(
        proto_example.check_abstract_message(message_1,
                                             message_1.DESCRIPTOR.full_name))

  @parameterized.named_parameters(
      ('int_message_unique_ptr', proto_example.get_int_message_unique_ptr()),
      ('abstract_message_unique_ptr',
       proto_example.get_abstract_message_unique_ptr()))
  def test_get_int_message_unique_ptr(self, message):
    message.value = 5
    self.assertEqual(message.value, 5)
    self.assertTrue(proto_example.check_int_message(message, 5))
    self.assertTrue(
        proto_example.check_abstract_message(message,
                                             message.DESCRIPTOR.full_name))

  def test_keep_alive_message(self):
    message = proto_example.make_test_message()
    field = message.int_message
    # message should be kept alive until field is also deleted.
    del message
    field.value = 5
    self.assertEqual(field.value, 5)

  def test_keep_alive_repeated(self):
    message = proto_example.make_test_message()
    field = message.repeated_int_value
    # message should be kept alive until field is also deleted.
    del message
    field.append(5)
    self.assertEqual(field[0], 5)

  def test_keep_alive_map(self):
    message = proto_example.make_test_message()
    field = message.string_int_map
    # message should be kept alive until field is also deleted.
    del message
    field['test'] = 5
    self.assertEqual(field['test'], 5)


if __name__ == '__main__':
  googletest.main()