"""test_colortogray.py - test the ColorToGray module
"""

import unittest
from StringIO import StringIO

import numpy as np
from cellprofiler.preferences import set_headless

set_headless()

import cellprofiler.pipeline as cpp
import cellprofiler.measurement as cpm
import cellprofiler.image as cpi
import cellprofiler.object as cpo

import cellprofiler.modules.injectimage as cpm_inject
import cellprofiler.modules.colortogray as cpm_ctg

import tests.modules as cpmt
from cellprofiler.workspace import Workspace

IMAGE_NAME = "image"
OUTPUT_IMAGE_F = "outputimage%d"


class TestColorToGray(unittest.TestCase):
    def get_my_image(self):
        """A color image with red in the upper left, green in the lower left and blue in the upper right"""
        img = np.zeros((50, 50, 3))
        img[0:25, 0:25, 0] = 1
        img[0:25, 25:50, 1] = 1
        img[25:50, 0:25, 2] = 1
        return img

    def test_00_00_init(self):
        x = cpm_ctg.ColorToGray()

    def test_01_01_combine(self):
        img = self.get_my_image()
        inj = cpm_inject.InjectImage("my_image", img)
        inj.module_num = 1
        ctg = cpm_ctg.ColorToGray()
        ctg.module_num = 2
        ctg.image_name.value = "my_image"
        ctg.combine_or_split.value = cpm_ctg.COMBINE
        ctg.red_contribution.value = 1
        ctg.green_contribution.value = 2
        ctg.blue_contribution.value = 3
        ctg.grayscale_name.value = "my_grayscale"
        pipeline = cpp.Pipeline()
        pipeline.add_module(inj)
        pipeline.add_module(ctg)
        pipeline.test_valid()

        measurements = cpm.Measurements()
        object_set = cpo.ObjectSet()
        image_set_list = cpi.ImageSetList()
        workspace = Workspace(pipeline, inj, None, None, measurements,
                              image_set_list, None)
        inj.prepare_run(workspace)
        inj.prepare_group(workspace, {}, [1])
        image_set = image_set_list.get_image_set(0)
        inj.run(Workspace(pipeline, inj, image_set, object_set, measurements, None))
        ctg.run(Workspace(pipeline, ctg, image_set, object_set, measurements, None))
        grayscale = image_set.get_image("my_grayscale")
        self.assertTrue(grayscale)
        img = grayscale.image
        self.assertAlmostEqual(img[0, 0], 1.0 / 6.0)
        self.assertAlmostEqual(img[0, 25], 1.0 / 3.0)
        self.assertAlmostEqual(img[25, 0], 1.0 / 2.0)
        self.assertAlmostEqual(img[25, 25], 0)

    def test_01_02_split_all(self):
        img = self.get_my_image()
        inj = cpm_inject.InjectImage("my_image", img)
        inj.module_num = 1
        ctg = cpm_ctg.ColorToGray()
        ctg.module_num = 2
        ctg.image_name.value = "my_image"
        ctg.combine_or_split.value = cpm_ctg.SPLIT
        ctg.use_red.value = True
        ctg.use_blue.value = True
        ctg.use_green.value = True
        ctg.red_name.value = "my_red"
        ctg.green_name.value = "my_green"
        ctg.blue_name.value = "my_blue"
        pipeline = cpp.Pipeline()
        pipeline.add_module(inj)
        pipeline.add_module(ctg)
        pipeline.test_valid()

        measurements = cpm.Measurements()
        object_set = cpo.ObjectSet()
        image_set_list = cpi.ImageSetList()
        workspace = Workspace(pipeline, inj, None, None, measurements,
                              image_set_list, None)
        inj.prepare_run(workspace)
        inj.prepare_group(workspace, {}, [1])
        image_set = image_set_list.get_image_set(0)
        inj.run(Workspace(pipeline, inj, image_set, object_set, measurements, None))
        ctg.run(Workspace(pipeline, ctg, image_set, object_set, measurements, None))
        red = image_set.get_image("my_red")
        self.assertTrue(red)
        img = red.image
        self.assertAlmostEqual(img[0, 0], 1)
        self.assertAlmostEqual(img[0, 25], 0)
        self.assertAlmostEqual(img[25, 0], 0)
        self.assertAlmostEqual(img[25, 25], 0)
        green = image_set.get_image("my_green")
        self.assertTrue(green)
        img = green.image
        self.assertAlmostEqual(img[0, 0], 0)
        self.assertAlmostEqual(img[0, 25], 1)
        self.assertAlmostEqual(img[25, 0], 0)
        self.assertAlmostEqual(img[25, 25], 0)
        blue = image_set.get_image("my_blue")
        self.assertTrue(blue)
        img = blue.image
        self.assertAlmostEqual(img[0, 0], 0)
        self.assertAlmostEqual(img[0, 25], 0)
        self.assertAlmostEqual(img[25, 0], 1)
        self.assertAlmostEqual(img[25, 25], 0)

    def test_01_03_combine_channels(self):
        np.random.seed(13)
        image = np.random.uniform(size=(20, 10, 5))
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        image_set.add(IMAGE_NAME, cpi.Image(image))

        module = cpm_ctg.ColorToGray()
        module.module_num = 1
        module.image_name.value = IMAGE_NAME
        module.combine_or_split.value = cpm_ctg.COMBINE
        module.grayscale_name.value = OUTPUT_IMAGE_F % 1
        module.rgb_or_channels.value = cpm_ctg.CH_CHANNELS
        module.add_channel()
        module.add_channel()

        channel_indexes = np.array([2, 0, 3])
        factors = np.random.uniform(size=3)
        divisor = np.sum(factors)
        expected = np.zeros((20, 10))
        for i, channel_index in enumerate(channel_indexes):
            module.channels[i].channel_choice.value = module.channel_names[channel_index]
            module.channels[i].contribution.value_text = "%.10f" % factors[i]
            expected += image[:, :, channel_index] * factors[i] / divisor

        pipeline = cpp.Pipeline()

        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.RunExceptionEvent))

        pipeline.add_listener(callback)
        pipeline.add_module(module)
        workspace = Workspace(pipeline, module, image_set, cpo.ObjectSet(),
                              cpm.Measurements(), image_set_list)
        module.run(workspace)
        pixels = image_set.get_image(module.grayscale_name.value).pixel_data
        self.assertEqual(pixels.ndim, 2)
        self.assertEqual(tuple(pixels.shape), (20, 10))
        np.testing.assert_almost_equal(expected, pixels)

    def test_01_04_split_channels(self):
        np.random.seed(13)
        image = np.random.uniform(size=(20, 10, 5))
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        image_set.add(IMAGE_NAME, cpi.Image(image))

        module = cpm_ctg.ColorToGray()
        module.module_num = 1
        module.image_name.value = IMAGE_NAME
        module.combine_or_split.value = cpm_ctg.SPLIT
        module.rgb_or_channels.value = cpm_ctg.CH_CHANNELS
        module.add_channel()
        module.add_channel()

        channel_indexes = np.array([1, 4, 2])
        for i, channel_index in enumerate(channel_indexes):
            module.channels[i].channel_choice.value = module.channel_names[channel_index]
            module.channels[i].image_name.value = OUTPUT_IMAGE_F % i

        pipeline = cpp.Pipeline()

        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.RunExceptionEvent))

        pipeline.add_listener(callback)
        pipeline.add_module(module)
        workspace = Workspace(pipeline, module, image_set, cpo.ObjectSet(),
                              cpm.Measurements(), image_set_list)
        module.run(workspace)
        for i, channel_index in enumerate(channel_indexes):
            pixels = image_set.get_image(module.channels[i].image_name.value).pixel_data
            self.assertEqual(pixels.ndim, 2)
            self.assertEqual(tuple(pixels.shape), (20, 10))
            np.testing.assert_almost_equal(image[:, :, channel_index], pixels)

    def test_2_5_load_v2(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:10308

ColorToGray:[module_num:1|svn_version:\'10300\'|variable_revision_number:2|show_window:True|notes:\x5B\x5D]
    Select the input image:DNA
    Conversion method:Combine
    Image type\x3A:Channels
    Name the output image:OrigGrayw
    Relative weight of the red channel:1
    Relative weight of the green channel:3
    Relative weight of the blue channel:5
    Convert red to gray?:Yes
    Name the output image:OrigRedx
    Convert green to gray?:Yes
    Name the output image:OrigGreeny
    Convert blue to gray?:Yes
    Name the output image:OrigBluez
    Channel count:3
    Channel number\x3A:Red\x3A 1
    Relative weight of the channel:1
    Image name\x3A:RedChannel1
    Channel number\x3A:Blue\x3A 3
    Relative weight of the channel:2
    Image name\x3A:GreenChannel2
    Channel number\x3A:Green\x3A 2
    Relative weight of the channel:3
    Image name\x3A:BlueChannel3
"""
        pipeline = cpp.Pipeline()

        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))

        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, cpm_ctg.ColorToGray))
        self.assertEqual(module.image_name, "DNA")
        self.assertEqual(module.combine_or_split, cpm_ctg.COMBINE)
        self.assertEqual(module.rgb_or_channels, cpm_ctg.CH_CHANNELS)
        self.assertEqual(module.grayscale_name, "OrigGrayw")
        self.assertEqual(module.red_contribution, 1)
        self.assertEqual(module.green_contribution, 3)
        self.assertEqual(module.blue_contribution, 5)
        self.assertTrue(module.use_red)
        self.assertTrue(module.use_green)
        self.assertTrue(module.use_blue)
        self.assertEqual(module.red_name, "OrigRedx")
        self.assertEqual(module.green_name, "OrigGreeny")
        self.assertEqual(module.blue_name, "OrigBluez")
        self.assertEqual(module.channel_count.value, 3)
        self.assertEqual(module.channels[0].channel_choice, module.channel_names[0])
        self.assertEqual(module.channels[1].channel_choice, module.channel_names[2])
        self.assertEqual(module.channels[2].channel_choice, module.channel_names[1])
        self.assertEqual(module.channels[0].contribution, 1)
        self.assertEqual(module.channels[1].contribution, 2)
        self.assertEqual(module.channels[2].contribution, 3)
        self.assertEqual(module.channels[0].image_name, "RedChannel1")
        self.assertEqual(module.channels[1].image_name, "GreenChannel2")
        self.assertEqual(module.channels[2].image_name, "BlueChannel3")
