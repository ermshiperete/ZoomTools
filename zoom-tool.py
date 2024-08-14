#!/usr/bin/python3

import argparse
import logging
import subprocess

def _get_zoom_window_id(name):
    result = subprocess.run(['xdotool', 'search', '--name', name], stdout=subprocess.PIPE)
    logging.debug(f'xdotool search --name "{name}": {result.stdout.decode("utf-8")}')
    if not (window_ids := result.stdout.decode('utf-8').splitlines()):
        return None  # No Zoom window found
    return window_ids[0]


def _activate_zoom_window(window_id, sync=True):
    # Bring the window to the foreground
    if sync:
        result = subprocess.run(['xdotool', 'windowactivate', '--sync', window_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
    else:
        result = subprocess.run(['xdotool', 'windowactivate', window_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
    return result.index('failed') < 0 if result else True


def bring_zoom_to_foreground():
    try:
        window_id = _get_zoom_window_id('Meeting')
        if not window_id:
            return False  # No Zoom window found

        if _activate_zoom_window(window_id, False):
            _activate_zoom_window(window_id, True)
        else:
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
            subprocess.run(['xdotool', 'mousemove', '--sync', str(click_x), str(click_y), 'click', '1'])

            # Bring the window to the foreground
            if not _activate_zoom_window(window_id, True):
                return False
        return True  # Zoom window found and brought to the foreground
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Zoom tools')
  parser.add_argument('--activate', action='store_true', help='Activate Zoom window')
  args = parser.parse_args()

  if args.activate:
    if bring_zoom_to_foreground():
        logging.info("Zoom Meeting window brought to the foreground.")
    else:
        logging.info("Zoom Meeting window not found.")
