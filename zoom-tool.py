#!/usr/bin/python3

import argparse
import logging
import subprocess
import time


def _get_zoom_window_id(name):
    result = subprocess.run(['xdotool', 'search', '--name', name], stdout=subprocess.PIPE)
    logging.debug(f'xdotool search --name "{name}": {result.stdout.decode("utf-8")}')
    if not (window_ids := result.stdout.decode('utf-8').splitlines()):
        return None  # No Zoom window found
    return window_ids[0]


def _bring_to_foreground(window_id, sync=True):
    # Bring the window to the foreground
    if sync:
        result = subprocess.run(['xdotool', 'windowactivate', '--sync', window_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
    else:
        result = subprocess.run(['xdotool', 'windowactivate', window_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
    return result.index('failed') < 0 if result else True


def _restore_zoom_window():
    mini_window_id = _get_zoom_window_id('zoom_linux_float_video_window')
    if not mini_window_id:
        return False  # No Zoom window found

    logging.debug(f"Window {mini_window_id}")
    # Check if the window is minimized
    result = subprocess.run(['xdotool', 'getwindowgeometry', mini_window_id], stdout=subprocess.PIPE)
    logging.debug(f'xdotool getwindowgeometry {mini_window_id}: {result.stdout.decode("utf-8")}')
    # Window 146800748
    #   Position: 396,153 (screen: 0)
    #   Geometry: 1190x802

    x = y = width = height = 0
    geometry = result.stdout.decode('utf-8').splitlines()
    for line in geometry:
        line = line.strip()
        if line.startswith('Position:'):
            parts = line.split(' ')
            pos = parts[1].split(',')
            x = int(pos[0])
            y = int(pos[1])
        elif line.startswith('Geometry:'):
            parts = line.split(' ')
            width = int(parts[1].split('x')[0])
            height = int(parts[1].split('x')[1])
    if width == 0 or height == 0:
        logging.warning(f"Window {mini_window_id} has invalid dimensions: {x}/{y} {width}x{height}")
        return False

    click_x = x + width - width * 0.1
    click_y = y + height - height * 0.1
    logging.debug(f"Clicking at {click_x}, {click_y}")
    subprocess.run(['xdotool', 'mousemove', '--sync', str(click_x), str(click_y), 'click', '1', 'sleep', '0.5', 'mousemove', '--sync', str(click_x-1), str(click_y-1), 'click', '1'])
    return True


def activate_window():
    # Another option would be:
    # m = xdotool search --name Meeting
    # xdotool windowmap $m
    # w = xdotool search --name "Zoom Workplace"
    # xdotool windowmap $w
    # d = xdotool get_desktop_for_window $m
    # xdotool set_desktop $d
    # xdotool windowactivate $m
    try:
        window_id = _get_zoom_window_id('Meeting')
        if not window_id:
            return False  # No Zoom window found

        if _bring_to_foreground(window_id, False):
            _bring_to_foreground(window_id, True)
        else:
            if not _restore_zoom_window():
                return False

            # Bring the window to the foreground
            if not _bring_to_foreground(window_id, True):
                return False
        return True  # Zoom window found and brought to the foreground
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False


def toggle_audio():
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'alt+a'])


def toggle_video():
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'alt+v'])


def end_meeting():
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'alt+F4'])


def get_current_active_window():
    result = subprocess.run(['xdotool', 'getactivewindow'], stdout=subprocess.PIPE)
    logging.debug(f'xdotool getactivewindow: {result.stdout.decode("utf-8")}')
    return result.stdout.decode('utf-8').strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Zoom tools')
    parser.add_argument('--activate', action='store_true', help='Activate Zoom window')
    parser.add_argument('--toggle-audio', action='store_true', help='Toggle audio')
    parser.add_argument('--toggle-video', action='store_true', help='Toggle video')
    parser.add_argument('--end-meeting', action='store_true', help='End meeting')
    args = parser.parse_args()

    current_window = get_current_active_window()

    if not activate_window():
        logging.info("Zoom Meeting window not found.")
        exit(1)

    if args.toggle_audio:
        toggle_audio()
    if args.toggle_video:
        toggle_video()
    if args.end_meeting:
        end_meeting()

    if not args.activate and not args.end_meeting:
        subprocess.run(['xdotool', 'windowactivate', '--sync', current_window])
