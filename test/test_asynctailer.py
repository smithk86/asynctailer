# add the project directory to the pythonpath
import os.path
import sys
from pathlib import Path
dir_ = Path(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, str(dir_.parent))

import asyncio
import time
from functools import partial

import pytest
from async_timeout import timeout

from asynctailer import AsyncTailer


dir_ = Path(os.path.dirname(os.path.abspath(__file__)))
sample_file = os.path.join(dir_, 'data', 'sample.txt')
sample_lines = ['Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent non elit at elit ultricies condimentum sed at ipsum. Nunc posuere sapien eget ex aliquet, ac mollis libero sollicitudin. Sed cursus lectus dui, nec rhoncus urna lobortis id. Etiam gravida sagittis est id tincidunt. Mauris a cursus metus. Maecenas feugiat nunc at rhoncus blandit. Mauris felis elit, pellentesque eget lobortis id, blandit quis dolor.', '', 'Nullam ante diam, ullamcorper sed bibendum ac, blandit in orci. Aenean auctor non est quis interdum. Nunc scelerisque elit ac massa tempor rutrum. Phasellus a tortor venenatis, tempor magna tempus, posuere justo. Praesent vestibulum diam erat, sit amet pharetra lectus hendrerit auctor. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam erat volutpat. Etiam non augue non sem placerat viverra. Morbi enim libero, consequat sed eros a, posuere sagittis mi. Pellentesque tempus elit et libero accumsan ullamcorper. Maecenas et suscipit lacus, ut placerat nunc. In hac habitasse platea dictumst. Quisque porta eget urna sed tristique. Phasellus sed risus tempus, efficitur sem eget, bibendum orci.', '', 'Fusce pellentesque ultricies maximus. Aliquam sed sem finibus nibh iaculis pellentesque. Quisque venenatis diam massa, eget aliquet dui accumsan quis. Proin id felis et dolor interdum mollis at ut felis. Praesent non nibh ac lorem congue egestas eget ut augue. Suspendisse sollicitudin vestibulum pharetra. Vivamus sit amet augue sed eros viverra fermentum. Suspendisse potenti.', '', 'Aenean ac urna dictum, tristique nisl vitae, tristique metus. Quisque ut augue congue, sodales diam eget, tempor nulla. Fusce et metus nisl. Aliquam elementum mollis mi. Cras fringilla elit a nisl vestibulum pellentesque maximus a lacus. Quisque commodo eget lectus sed venenatis. Praesent mollis elementum efficitur. In augue augue, elementum et augue vel, condimentum interdum lorem. Praesent nec mi aliquam, ultrices sem non, dignissim velit. Nam sed congue erat. Nullam ultrices dictum malesuada.', '', 'Nam ultricies in libero ac imperdiet. Duis nibh leo, euismod eu risus ac, finibus cursus metus. Fusce in varius urna. Curabitur posuere id dui eu lobortis. Sed eget aliquet felis, in fringilla sapien. Nulla ultricies mattis nunc vitae tincidunt. Curabitur in pellentesque mauris. Nullam accumsan mi sit amet dignissim finibus. Donec aliquet magna quis neque maximus, et gravida ligula posuere. In mollis ultricies gravida. Proin non leo eros. Nullam nec metus id odio aliquam ullamcorper ut eu nulla. Nunc quam arcu, dictum a velit nec, varius placerat nibh.']


@pytest.mark.asyncio
async def test_head():
    # test head() with lines=2
    with open(sample_file, 'r') as fh:
        tailer = AsyncTailer(fh)
        lines = await tailer.head(2)
        assert len(lines) == 3
        for i, line in enumerate(lines):
            assert line == sample_lines[i]
    # test head() with lines=10
    with open(sample_file, 'r') as fh:
        tailer = AsyncTailer(fh)
        lines = await tailer.head(10)
        assert len(lines) == 9
        for i, line in enumerate(lines):
            assert line == sample_lines[i]


@pytest.mark.asyncio
async def test_tail():
    # test tail() with lines=2
    tailed_sample_lines = sample_lines[-2:]
    with open(sample_file, 'r') as fh:
        tailer = AsyncTailer(fh)
        lines = await tailer.tail(2)
        assert len(lines) == 2
        for i, line in enumerate(lines):
            assert line == tailed_sample_lines[i]
    # test tail() with lines=5
    tailed_sample_lines = sample_lines[-5:]
    with open(sample_file, 'r') as fh:
        tailer = AsyncTailer(fh)
        lines = await tailer.tail(5)
        assert len(lines) == 5
        for i, line in enumerate(lines):
            assert line == tailed_sample_lines[i]
    # test tail() with lines=10
    with open(sample_file, 'r') as fh:
        tailer = AsyncTailer(fh)
        lines = await tailer.tail(10)
        assert len(lines) == 9
        for i, line in enumerate(lines):
            assert line == sample_lines[i]


@pytest.mark.asyncio
async def test_follow():
    def write_file(filename):
        with open(sample_file, 'r') as fh:
            with open(filename, 'w') as fhw:
                for line in fh.readlines():
                    time.sleep(.25)
                    print(line, end='', file=fhw, flush=True)

    loop = asyncio.get_running_loop()
    sample_lines_iter = iter([line for line in sample_lines if len(line) > 0])

    try:
        output_file = Path(os.path.join(dir_, 'data', 'sample-write.txt'))
        output_file.touch()
        task = loop.run_in_executor(None, partial(write_file, output_file))
        try:
            async with timeout(4) as t:
                with open(output_file, 'r') as fh:
                    async for line in AsyncTailer(fh).follow():
                        if len(line) > 0:
                            assert line == next(sample_lines_iter)
        except asyncio.TimeoutError:
            pass

        # confirm the iterater is exausted
        with pytest.raises(StopIteration):
            next(sample_lines_iter)

        await task
    finally:
        if os.path.isfile(output_file):
            output_file.unlink()
