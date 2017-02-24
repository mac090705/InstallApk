#! python3

import sys
import os
import re
import traceback
from subprocess import Popen, PIPE
import tkinter as tk
from tkinter import filedialog


def get_device_array():
    device_cmd = 'adb devices'
    ret = os.popen(device_cmd).read()
    ret, num = re.subn('\*.+\*', '', ret)
    ret = ret.replace('List of devices attached', '').replace('device', '').strip()
    device_array = re.split('\s+', ret)
    return device_array


def get_device_overview(index, serial_number):
    base_cmd = 'adb -s %s shell getprop ' % serial_number
    ret = os.popen(base_cmd + 'ro.product.manufacturer')
    manufacturer = ret.read().strip()
    ret = os.popen(base_cmd + 'ro.product.model')
    model = ret.read().strip()
    ret = os.popen(base_cmd + 'ro.build.version.release')
    release = ret.read().strip()
    ret = os.popen(base_cmd + 'ro.build.version.sdk')
    sdk = ret.read().strip()
    return '  '.join([str(index + 1).ljust(5), manufacturer.ljust(12), model.ljust(15), release.ljust(7), sdk.ljust(3),
                      serial_number.ljust(15)])


def check_and_install(apk_path):
    device_array = get_device_array()
    count = len(device_array)
    if count > 1:
        print('当前已连接%d台设备:' % count)
        print('  '.join(
            ['Index'.ljust(5), 'Manufacturer'.ljust(12), 'Model'.ljust(15), 'Release'.ljust(7), 'SDK'.ljust(3),
             'SN'.ljust(15)]))
        for i in range(count):
            print(get_device_overview(i, device_array[i]))
        index = input('请选择要安装的设备Index（输入0表示同时安装）：')
        while not index.isdigit():
            index = input('输入不合法，请重新输入：')
        while int(index) > count or int(index) < 0:
            index = input('输入不合法，请重新输入：')
        if int(index) == 0:
            for device in device_array:
                install(device, apk_path)
        else:
            install(device_array[int(index) - 1], apk_path)
    else:
        install(device_array[0], apk_path)


def install(serial_number, apk_path):
    p = Popen(['adb', '-s', serial_number, 'install', '-r', apk_path], stdout=PIPE)
    while True:
        line = p.stdout.readline()
        print(str(line, 'utf-8').strip())
        if not line:
            break
    launch(serial_number, apk_path)


def launch(number, apk_path):
    ret = os.popen('aapt dump badging %s' % apk_path).read()
    info_list = re.split('\n', ret)
    package = ''
    activity = ''
    for info in info_list:
        if info.startswith('package'):
            package_array = re.split('\s', info)
            for item in package_array:
                if item.startswith('name='):
                    package = item[6:len(item) - 1]
                    break
        elif info.startswith('launchable-activity'):
            activity_array = re.split('\s', info)
            for item in activity_array:
                if item.startswith('name='):
                    activity = item[6:len(item) - 1]
                    if activity.startswith(package):
                        activity = re.subn(package, '', activity)[0]
                    break
    if package and activity:
        ret = os.popen('adb -s %s shell am start %s/%s' % (number, package, activity))
        print(ret.read())


def is_apk_file_valid(path):
    return path[-4:].strip() == '.apk'


def run():
    try:
        if len(sys.argv) > 1 and sys.argv[1]:
            apk_path = sys.argv[1]
        else:
            root = tk.Tk()
            root.withdraw()
            apk_path = filedialog.askopenfilename(title='选择apk文件', filetypes=(('apk file', '*.apk'),))
        if not apk_path:
            exit()
        else:
            if is_apk_file_valid(apk_path):
                print('正在安装：%s' % apk_path)
                check_and_install(apk_path)
            else:
                print('无效的apk文件')
        input('Press <Enter> to exit')
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        input()


run()
