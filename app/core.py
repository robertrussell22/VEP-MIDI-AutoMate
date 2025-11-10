###
# VEP MIDI AutoMate 1.0 core.py
# https://github.com/robertrussell22/VEP-MIDI-AutoMate
###

import sys, time, datetime, ctypes, mss, csv
from ctypes import wintypes
from PIL import ImageChops
from pathlib import Path
import pygetwindow as gw
import pyautogui as pag

class VEP_MIDI_AutoMate_Error(Exception): pass

class VEP_MIDI_AutoMate_Abort(Exception): pass

def screenshot(scope='window', window_origin=None, window_size=None, region=None):
    # takes a screenshot
    with mss.mss() as sct:
        if region:
            left, top, right, bottom = region
            bounding_box = {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}
        else:
            if scope == 'desktop':
                monitor = sct.monitors[0]
                bounding_box = {'left': monitor['left'], 'top': monitor['top'], 'width': monitor['width'], 'height': monitor['height']}
            else:
                bounding_box = {'left': window_origin[0], 'top': window_origin[1], 'width': window_size[0], 'height': window_size[1]}
        screen_grab = sct.grab(bounding_box)
        from PIL import Image as PILImage
        image = PILImage.frombytes('RGB', screen_grab.size, screen_grab.rgb)
        return image

def crop_by_largest_difference(image_before, image_after, extract_last_menu_only=False):
    # extracts the image of a new submenu by comparing image_before and image_after
    try:
        mask = ImageChops.difference(image_before, image_after).point(lambda x: 255 if x > 25 else 0)
        width, height = mask.size
        mask_binary = mask.convert('1')
        pixel = mask_binary.load()
        x_bounds = []
        in_x_bounds = False
        x_bounds_start = -1
        for x in range(width):
            for y in range(height):
                if pixel[x, y] and not in_x_bounds:
                    in_x_bounds = True
                    x_bounds_start = x
                    break
                if pixel[x, y] and in_x_bounds:
                    break
            if y == height - 1 and in_x_bounds:
                in_x_bounds = False
                x_bounds.append((x_bounds_start, x, x - x_bounds_start))
        sorted_x_bounds = sorted(x_bounds, key=lambda x: x[2], reverse=True)
        largest_x_bounds = sorted_x_bounds[0]
        left = largest_x_bounds[0]
        right = largest_x_bounds[1]
        top = height + 1
        bottom = -1
        for x in range(left, right):
            for y in range(height):
                if pixel[x, y]:
                    break
            if y < top:
                top = y
            for y in reversed(range(height)):
                if pixel[x, y]:
                    break
            if y > bottom:
                bottom = y
    
        if extract_last_menu_only:
            initial_crop = image_after.crop((left, top, right, bottom + 1))
            initial_crop_gray = initial_crop.convert('L')
            pixel = initial_crop_gray.load()
            new_relative_left = -1
            for x in reversed(range(initial_crop.width - 1)):
                if abs(pixel[x-1,1] - pixel[x,0]) < 50:
                    new_relative_left = x-1
                    break
            bounding_box = (left + new_relative_left, top, right, bottom + 1)
        else:
            bounding_box = (left, top, right, bottom + 1)

        return image_after.crop(bounding_box), bounding_box
    except Exception:
        raise VEP_MIDI_AutoMate_Error('Something went wrong. Possibly a popup on your screen confused the algorithm. Please close and try again.')

def count_colour_bands(image, start_position, direction):
    # counts the colour bands in image from start_position in direction
    x, y = start_position
    pixel = image.load()
    width = image.size[0]
    height = image.size[1]
    p = (-1, -1, -1)
    count = 0
    while 0 <= x < width and 0 <= y < height:
        previous_p = p
        p = pixel[x,y]
        if p != previous_p:
            count += 1
        x += direction[0]
        y += direction[1]
    return count

def find_nth_colour_band(image, n, start_position, direction):
    # searches image from start_position in direction until the nth new colour band
    x, y = start_position
    target_band_number = n

    pixel = image.load()

    width = image.size[0]
    height = image.size[1]

    band_number = -1
    target_band_start = (-1, -1)
    target_band_end = (-1, -1)
    p = (-1, -1, -1)
    while 0 <= x < width and 0 <= y < height:
        previous_p = p
        p = pixel[x,y]
        if p != previous_p:
            target_band_end = (x - direction[0], y - direction[1])
            if band_number == target_band_number:
                target_band_middle = (int((target_band_start[0] + target_band_end[0])/2), int((target_band_start[1] + target_band_end[1])/2))
                return (target_band_start, target_band_middle, target_band_end)
            else:
                target_band_start = (x, y)
            band_number += 1
        x += direction[0]
        y += direction[1]
    return ((-1,-1), (-1,-1), (-1,-1))

def wait_for_device_menu_to_open(grey_pixel, time_out=10.0):
    # waits for the device menu to open, determined by a change in a specific pixel's colour 
    x, y = pag.position()
    detected_pixel = (-1, -1, -1)
    t_0 = time.perf_counter()
    while detected_pixel != grey_pixel and time.perf_counter() - t_0 < time_out:
        time.sleep(0.003)
        detected_pixel = screenshot(scope='desktop', region=(x-1, y, x, y+1)).getpixel((0,0))
    if time.perf_counter() - t_0 > time_out:
        raise VEP_MIDI_AutoMate_Error('Something went wrong. Make sure that your VEP mixer is set up properly, with correctly names channels, plugins, etc. Please close and try again.')

def wait_for_menu_item_to_turn_blue(blue_pixel, item_height, time_out=10.0):
    # waits until the background of a menu item turns blue, indicating that the menu item is ready to be selected
    x, y = pag.position()
    t_0 = time.perf_counter()
    offset = 0
    blue_pixel_detected = False
    while not blue_pixel_detected and time.perf_counter() - t_0 < time_out:
        time.sleep(0.003)
        for offset in range(item_height // 2):
            if screenshot(scope='desktop', region=(x-1, y+offset, x, y+offset+1)).getpixel((0,0)) == blue_pixel or screenshot(scope='desktop', region=(x-1, y-offset, x, y-offset+1)).getpixel((0,0)) == blue_pixel:
                blue_pixel_detected = True
    if time.perf_counter() - t_0 > time_out:
        raise VEP_MIDI_AutoMate_Error('Something went wrong. Make sure that your VEP mixer is set up properly, with correctly names channels, plugins, etc. Please close and try again.')

def check_abort(abort_event):
    # checks for the abort event
    if abort_event and abort_event.is_set():
        raise VEP_MIDI_AutoMate_Abort('Manually aborted. You can start again when you\'re ready.')

def go(path, abort_event, slow_mode, update_callback, required_headers, BULLET):
    
    # import CSV file
    update_callback(f'{BULLET} importing CSV file')
    data = []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise VEP_MIDI_AutoMate_Error('CSV appears empty or has no header row. Expected columns: ' + ','.join(required_headers) + '. Consider using the template provided.')
        missing_headers = [header for header in required_headers if header not in reader.fieldnames]
        if missing_headers:
            raise VEP_MIDI_AutoMate_Error('CSV is missing required columns: ' + ','.join(missing_headers) + '. Consider using the template provided.')
        for _, raw_data in enumerate(reader, start=2):
            raw_datum = {(k or '').strip().lower(): (v or '').strip() for k, v in raw_data.items()}
            data.append(raw_datum)
    check_abort(abort_event)

    # auto gui settings
    pag.FAILSAFE = True
    if slow_mode:
        pag.PAUSE = 0.5
    else:
        pag.PAUSE = 0.03
    check_abort(abort_event)

    # find Vienna Ensemble Pro (VEP) window
    update_callback(f'{BULLET} locating and preparing VEP')
    window_found = False
    for window in gw.getAllWindows():
        if window.title.startswith('Vienna Ensemble Pro'):
            window_found = True
            break
    if not window_found:
        raise VEP_MIDI_AutoMate_Error('Vienna Ensemble Pro window not found. Please ensure Vienna Ensemble Pro is open.')
    check_abort(abort_event)

    # determine VEP window type
    window_type = None
    if 'Standalone' in window.title:
        window_type = 'standalone'
    elif 'Server' in window.title:
        window_type = 'server'
    else:
        raise VEP_MIDI_AutoMate_Error('Unrecognised Vienna Ensemble Pro window type.')
    check_abort(abort_event)

    # maximise VEP window
    if sys.platform != 'win32':
        raise OSError('Currently supports Windows only.')
    try:
        window.maximize()
    except Exception:
        raise VEP_MIDI_AutoMate_Error('Something went wrong. Couldn\'t maximise the Vienna Ensemble Pro window.')
    check_abort(abort_event)

    # bring VEP window to front
    try:
        window.activate()
    except Exception:
        raise VEP_MIDI_AutoMate_Error('Something went wrong. Couldn\'t activate the Vienna Ensemble Pro window.')
    check_abort(abort_event)

    # get virtual desktop origin
    with mss.mss() as sct:
        virtual_desktop = sct.monitors[0]  # whole desktop
        desktop_origin = (virtual_desktop['left'], virtual_desktop['top'])
    check_abort(abort_event)

    # get VEP window origin, width and height
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    window_handle = getattr(window, '_hWnd', None)
    if window_handle is None:
        raise RuntimeError('Could not obtain HWND from window object')
    class RECTANGLE(ctypes.Structure):
        _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]
    class POINT(ctypes.Structure):
        _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)] 
    rectangle = RECTANGLE()
    if not ctypes.windll.user32.GetClientRect(window_handle, ctypes.byref(rectangle)):
        raise RuntimeError('GetClientRect failed')
    top_left = POINT(0, 0)
    bottom_right = POINT(rectangle.right, rectangle.bottom)
    if not ctypes.windll.user32.ClientToScreen(window_handle, ctypes.byref(top_left)):
        raise RuntimeError('ClientToScreen(top_left) failed')
    if not ctypes.windll.user32.ClientToScreen(window_handle, ctypes.byref(bottom_right)):
        raise RuntimeError('ClientToScreen(bottom_right) failed')
    window_origin = (top_left.x, top_left.y)
    window_width = bottom_right.x - top_left.x
    window_height = bottom_right.y - top_left.y
    window_size = (window_width, window_height)
    check_abort(abort_event)

    # confirm VEP instances
    image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
    if window_type == 'server':
        colour_bands_left = count_colour_bands(image, (0, 0), (0, 1))
        if colour_bands_left == 1:
            raise VEP_MIDI_AutoMate_Error('Vienna Ensemble Pro must have at least one instance.')
    check_abort(abort_event)

    # remove unnecessary sub-windows
    pag.keyDown("alt")
    pag.press("h") # Help menu
    pag.keyUp("alt")
    pag.press('left') # View menu
    for _ in range(7):
        pag.press('down')
    pag.press('enter') # Reset Windows
    pag.press('f2') # hide Channels
    pag.press('f3') # hide Mixer
    for window_temp in gw.getAllWindows():
        if window_temp.title == 'Group Settings':
            pag.press('f8') # hide Group Settings
            break
    check_abort(abort_event)

    # ensure MIDI Controllers is selected
    image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
    _, (_, y), _ = find_nth_colour_band(image=image, n=3, start_position=(window_width-1, 0), direction=(0, 1)) # fourth (n=3) colour down from the top-right
    _, (x, _), _ = find_nth_colour_band(image=image, n=2, start_position=(window_width-1, y), direction=(-1, 0)) # then third (n=2) colour to the left
    pag.moveTo(window_origin[0] + x, window_origin[1] + y)
    pag.click()
    check_abort(abort_event)
    
    # ensure all rows are deleted
    update_callback(f'{BULLET} deleting current rows')
    image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
    (x_start, y_start) = (x, y)
    number_of_colours = count_colour_bands(image=image, start_position=(x_start, y_start), direction=(0, 1))
    while number_of_colours > 4:
        _, _, (_, y) = find_nth_colour_band(image=image, n=3, start_position=(x_start, y_start), direction=(0, 1))
        _, (x, _), _ = find_nth_colour_band(image=image, n=2, start_position=(x_start, y), direction=(-1, 0))
        pag.click(window_origin[0] + x, window_origin[1] + y)
        image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
        number_of_colours = count_colour_bands(image=image, start_position=(x_start, y_start), direction=(0, 1))
        check_abort(abort_event)

    # start empty row
    band_number = 4 if window_type == 'standalone' else 6 if window_type == 'server' else -1
    _, _, (_, y) = find_nth_colour_band(image=image, n=band_number, start_position=(0, 0), direction=(0, 1))
    _, (x, _), _ = find_nth_colour_band(image=image, n=0, start_position=(0, y), direction=(1, 0))
    _, (_, y), _ = find_nth_colour_band(image=image, n=3, start_position=(x, y), direction=(0, 1))
    new_row_click_location = (x, y)
    pag.moveTo(window_origin[0] + new_row_click_location[0], window_origin[1] + new_row_click_location[1])
    pag.click()
    check_abort(abort_event)

    # click to reveal menu Level 1
    update_callback(f'{BULLET} investigating layout')
    x, y = new_row_click_location
    image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
    _, (_, y), _ = find_nth_colour_band(image=image, n=4, start_position=(x, y), direction=(0, 1))
    grey_pixel = image.getpixel((x-1, y))
    pag.moveTo(window_origin[0] + x, window_origin[1] + y)
    image_before = screenshot(scope='desktop')
    pag.click()
    wait_for_device_menu_to_open(grey_pixel)
    image_after = screenshot(scope='desktop')
    device_menu, bounding_box = crop_by_largest_difference(image_before, image_after)
    check_abort(abort_event)

    # determine number of items in menu level 1
    pixel = device_menu.load()
    for x in range(device_menu.width - 1, 0, -1):
        (_,y), _, _ = find_nth_colour_band(image=device_menu, n=2, start_position=(x,0), direction=(0,1))
        if y > -1:
            x_triangle_right = x
            y_triangle_right = y
            break
    pixel_black = pixel[x_triangle_right + 1, y_triangle_right]
    for x in range(x_triangle_right, 0, -1):
        if pixel[x, y_triangle_right] == pixel_black:
            x_triangle_left = x + 1
            y_triangle_left = y_triangle_right
            break
    for y in range(y_triangle_left, 0, -1):
        if pixel[x_triangle_left, y] == pixel_black:
            y_triangle_top = y + 1
            break
    for y in range(y_triangle_left, device_menu.height, 1):
        if pixel[x_triangle_left, y] == pixel_black:
            y_triangle_bottom = y - 1
            break
    triangle_image = device_menu.crop((x_triangle_left - 1, y_triangle_top - 1, x_triangle_right + 2, y_triangle_bottom + 2))
    number_of_items = 0
    columns_x = []
    device_positions = {}
    for x in range(0, device_menu.width):
        for y in range(0, device_menu.height):
            candidate_triangle_image = device_menu.crop((x, y, x + triangle_image.width, y + triangle_image.height))
            comparison = ImageChops.difference(candidate_triangle_image, triangle_image)
            if not comparison.getbbox():
                number_of_items += 1
                columns_x.append(x)
                device_positions[number_of_items] = (x,y)
    column_dictionary_x = dict(sorted((column_x, columns_x.count(column_x)) for column_x in columns_x))
    number_of_device_columns = len(column_dictionary_x)
    number_of_devices = dict(zip(range(len(column_dictionary_x)), list(column_dictionary_x.values())))
    check_abort(abort_event)

    # calculate average item height
    average_item_height = int(round((device_menu.height-1)/(number_of_devices[0] + 1)))
    check_abort(abort_event)

    # calculate all left-column menu widths
    device_menu_width = device_menu.width
    image_device = screenshot(scope='desktop')
    pag.moveTo(desktop_origin[0] + bounding_box[0] + device_menu_width // number_of_device_columns // 2, desktop_origin[1] + bounding_box[1] + int(0.5*average_item_height))
    blue_pixel = screenshot(scope='desktop', region=(desktop_origin[0] + bounding_box[0] + device_menu_width // number_of_device_columns // 2, desktop_origin[1] + bounding_box[1] + int(0.5*average_item_height), desktop_origin[0] + bounding_box[0] + device_menu_width // number_of_device_columns // 2 + 1, desktop_origin[1] + bounding_box[1] + int(0.5*average_item_height) + 1)).getpixel((0,0))
    pag.moveTo(desktop_origin[0] + bounding_box[0] + device_menu_width // number_of_device_columns // 2, desktop_origin[1] + bounding_box[1] + int(1.5*average_item_height))
    wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
    image_channel = screenshot(scope='desktop')
    _, bounding_box = crop_by_largest_difference(image_device, image_channel, extract_last_menu_only=True)
    channel_menu_width = int(bounding_box[2] - bounding_box[0])
    pag.moveTo(desktop_origin[0] + bounding_box[0] + channel_menu_width // 2, desktop_origin[1] + bounding_box[1] + int(0.5*average_item_height))
    wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
    image_controller_group = screenshot(scope='desktop')
    _, bounding_box = crop_by_largest_difference(image_channel, image_controller_group, extract_last_menu_only=True)
    controller_group_menu_width = int(bounding_box[2] - bounding_box[0])
    pag.moveTo(desktop_origin[0] + bounding_box[0] + controller_group_menu_width // 2, desktop_origin[1] + bounding_box[1] + int(0.5*average_item_height))
    wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
    image_cc = screenshot(scope='desktop')
    _, bounding_box = crop_by_largest_difference(image_controller_group, image_cc, extract_last_menu_only=True)
    cc_menu_width = int(bounding_box[2] - bounding_box[0])
    total_menu_width = device_menu_width + channel_menu_width + controller_group_menu_width + cc_menu_width
    screen_height = image_device.height
    check_abort(abort_event)

    # reset
    for _ in range(4):
        pag.press('escape')
    check_abort(abort_event)

    # locate important positions
    image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
    (_, first_row_top_y), (_, first_row_y), _ = find_nth_colour_band(image=image, n=4, start_position=new_row_click_location, direction=(0,1))
    _, _, (left_menu_left_x, _) = find_nth_colour_band(image=image, n=0, start_position=(new_row_click_location[0], first_row_top_y), direction=(-1,0))
    _, _, (left_menu_right_x, _) = find_nth_colour_band(image=image, n=0, start_position=(new_row_click_location[0], first_row_top_y), direction=(1,0))
    left_menu_x = int((left_menu_left_x + left_menu_right_x)/2)
    _, (right_menu_x, _), _ = find_nth_colour_band(image=image, n=4, start_position=(new_row_click_location[0], first_row_top_y), direction=(1,0))
    _, _, (_, bottom_gray_y) = find_nth_colour_band(image=image, n=0, start_position=(window_size[0]-1, window_size[1]-1), direction=(0,-1))
    initial_colours_along_top_row = count_colour_bands(image=image, start_position=(0,first_row_top_y), direction=(1,0))
    vertical_scrollbar_in_use = False
    vertical_scrollbar_x = -1
    vertical_scrollbar_y = -1
    check_abort(abort_event)

    # main loop
    update_callback(f'{BULLET} inputting data for {len(data)} rows')
    start_time = time.time()
    elapsed_time = 0
    for row_number in range(len(data)):

        # send progress update
        if row_number > 0:
            elapsed_time = time.time() - start_time
            estimated_time_required = elapsed_time / row_number * len(data)
        update_string = f' {row_number + 1}/{len(data)} {"∞:∞∞:∞∞" if row_number==0 else datetime.timedelta(seconds = int(estimated_time_required - elapsed_time))} ({data[row_number]["device"]},{data[row_number]["channel"]},{data[row_number]["cc"]}) → {data[row_number]["layer 1"]}/{data[row_number]["layer 2"]}{"/" if data[row_number]["layer 3"] else ""}{data[row_number]["layer 3"]}{"/" if data[row_number]["layer 4"] else ""}{data[row_number]["layer 4"]}'
        if data[row_number]['repeat']:
            update_string += f'(R{data[row_number]["repeat"]})'
        update_callback(update_string)

        # create new row
        if row_number > 0:
            pag.moveTo(window_origin[0] + new_row_click_location[0], window_origin[1] + new_row_click_location[1])
            pag.click()

            # scroll down if required
            image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
            if not vertical_scrollbar_in_use:
                if count_colour_bands(image=image, start_position=(0,first_row_top_y), direction=(1,0)) != initial_colours_along_top_row:
                    vertical_scrollbar_in_use = True
                    _, (vertical_scrollbar_x, _), _ = find_nth_colour_band(image=image, n=1, start_position=(window_size[0]-1,first_row_y), direction=(-1,0))
            if vertical_scrollbar_in_use:
                pixel = image.load()
                black_pixel = pixel[vertical_scrollbar_x, new_row_click_location[1]]
                found_vertical_scrollbar = False
                vertical_scrollbar_y_start = -1
                vertical_scrollbar_y_end = -1
                for y in range(new_row_click_location[1], window_size[1]):
                    p = pixel[vertical_scrollbar_x,y]
                    if found_vertical_scrollbar and abs(p[0] - black_pixel[0]) + abs(p[1] - black_pixel[1]) + abs(p[2] - black_pixel[2]) < 5 :
                        vertical_scrollbar_y_end = y
                        break
                    if not found_vertical_scrollbar and abs(p[0] - black_pixel[0]) + abs(p[1] - black_pixel[1]) + abs(p[2] - black_pixel[2]) >= 5 :
                        vertical_scrollbar_y_start = y
                        found_vertical_scrollbar = True
                vertical_scrollbar_y = int((vertical_scrollbar_y_start+vertical_scrollbar_y_end)/2)
                pag.moveTo(window_origin[0] + vertical_scrollbar_x, window_origin[1] + vertical_scrollbar_y + 1)
                pag.dragTo(window_origin[0] + vertical_scrollbar_x, window_origin[1] + window_size[1]-1)
            check_abort(abort_event)   

        # click on new row
        image = screenshot(scope='window', window_origin=window_origin, window_size=window_size)
        _, (_, last_row_y), _ = find_nth_colour_band(image=image, n=3, start_position=(new_row_click_location[0], bottom_gray_y), direction=(0,-1))
        pag.moveTo(window_origin[0] + left_menu_x, window_origin[1] + last_row_y)
        menu_region = (window_origin[0] + left_menu_x, desktop_origin[1], window_origin[0] + left_menu_x + total_menu_width, desktop_origin[1] + screen_height)
        image_main = screenshot(scope='desktop', region=menu_region)
        pag.click()
        wait_for_device_menu_to_open(grey_pixel)
        check_abort(abort_event)

        # select device
        device_position_x, device_position_y = device_positions[int(data[row_number]['device'])]
        image_device = screenshot(scope='desktop', region=menu_region)
        _, bounding_box = crop_by_largest_difference(image_main, image_device)
        pag.moveTo(menu_region[0] + bounding_box[0] + device_position_x, menu_region[1] + bounding_box[1] + device_position_y)
        wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
        check_abort(abort_event)

        # select channel
        image_channel = screenshot(scope='desktop', region=menu_region)
        _, bounding_box = crop_by_largest_difference(image_device, image_channel, extract_last_menu_only=True)
        channel_position_x = int((bounding_box[2] - bounding_box[0])/2)
        channel_position_y = int((int(data[row_number]['channel']) - 0.5) * average_item_height)
        pag.moveTo(menu_region[0] + bounding_box[0] + channel_position_x, menu_region[1] + bounding_box[1] + channel_position_y)
        wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
        check_abort(abort_event)

        # select controller group
        image_controller_group = screenshot(scope='desktop', region=menu_region)
        _, bounding_box = crop_by_largest_difference(image_channel, image_controller_group, extract_last_menu_only=True)
        controller_group_position_x = int((bounding_box[2] - bounding_box[0])/2)
        controller_group_position_y = int((int(data[row_number]['cc']) // 16 + 0.5) * average_item_height)
        pag.moveTo(menu_region[0] + bounding_box[0] + controller_group_position_x, menu_region[1] + bounding_box[1] + controller_group_position_y)
        wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
        check_abort(abort_event)

        # select cc
        image_cc = screenshot(scope='desktop', region=menu_region)
        _, bounding_box = crop_by_largest_difference(image_controller_group, image_cc, extract_last_menu_only=True)
        cc_position_x = int((bounding_box[2] - bounding_box[0])/2)
        cc_position_y = int((int(data[row_number]['cc']) % 16 + 0.5) * average_item_height)
        pag.moveTo(menu_region[0] + bounding_box[0] + cc_position_x, menu_region[1] + bounding_box[1] + cc_position_y)
        wait_for_menu_item_to_turn_blue(blue_pixel, average_item_height)
        pag.click()
        check_abort(abort_event)

        # click on right menu
        pag.moveTo(window_origin[0] + right_menu_x, window_origin[1] + last_row_y)
        pag.click()
        check_abort(abort_event)

        # input layer 1
        pag.write(data[row_number]['layer 1'])
        pag.press('down')
        check_abort(abort_event)

        # input layer 2
        pag.hotkey('ctrl','a')
        pag.press('delete')
        pag.write(data[row_number]['layer 2'])
        pag.press('down')
        check_abort(abort_event)

        # input layer 3
        if data[row_number]['layer 3']:
            pag.hotkey('ctrl','a')
            pag.press('delete')
            pag.write(data[row_number]['layer 3'])
            pag.press('down')
            if not data[row_number]['layer 4'] and data[row_number]['repeat']:
                for _ in range(int(data[row_number]['repeat'])):
                    pag.press('down')
            check_abort(abort_event)

            # input layer 4
            if data[row_number]['layer 4']:
                pag.hotkey('ctrl','a')
                pag.press('delete')
                pag.write(data[row_number]['layer 4'])
                pag.press('down')
                if data[row_number]['repeat']:
                    for _ in range(int(data[row_number]['repeat'])):
                        pag.press('down')
                pag.press('enter')
            else:
                pag.press('enter')
            check_abort(abort_event)

        else:
            pag.press('enter')
            check_abort(abort_event)
    
    if len(data) > 0:
        update_callback(f'Total time = {datetime.timedelta(seconds = int(elapsed_time))}.')
        update_callback(f'Average time per row ≈ {round(elapsed_time/len(data), 2)} seconds.')
        update_callback(f'All done.')
    else:
        update_callback(f'No rows found in the CSV.')