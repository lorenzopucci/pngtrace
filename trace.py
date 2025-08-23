from PIL import Image
import numpy as np
from random import randint
from math import floor
import json
import sys


DEBUG = True
COLOR_TRESHOLD = 100
RESOLUTION = 28
TRESHOLD = 0.02
COLLAPSE = 10000
HIGHLIGHT_REGION = 10


sys.setrecursionlimit(50000000)


def dist_2d(u, v):
    return sum([(int(u[i]) - int(v[i])) ** 2 for i in range(0, 2)])


def dist_4d(u, v):
    return sum([(int(u[i]) - int(v[i])) ** 2 for i in range(0, 4)])


def trace_png(arr):
    h, w, _ = arr.shape
    comp = np.zeros((h, w)) # the component assigned to each pixel
    preview_data = np.zeros((h, w, 3), dtype = np.uint8)


    # colors a small square centered at the given point in the preview
    def highlight(p, color = (255, 255, 255)):
        x, y = p
        for i in range(x - HIGHLIGHT_REGION, x + HIGHLIGHT_REGION):
            for j in range(y - HIGHLIGHT_REGION, y + HIGHLIGHT_REGION):
                preview_data[j][i] = color


    def is_in_border(x, y, ref):
        if dist_4d(arr[y][x], ref) > COLOR_TRESHOLD:
            return False

        for x1 in [x - 1, x, x + 1]:
            for y1 in [y - 1, y, y + 1]:
                if dist_4d(arr[y1][x1], ref) > COLOR_TRESHOLD:
                    return True
        return False


    # the dfs that assigns each pixel its connected component
    def assign_component(x, y, comp_idx, ref, preview_color):
        if dist_4d(arr[y][x], ref) > COLOR_TRESHOLD:
            return
        
        comp[y][x] = comp_idx
        preview_data[y][x] = preview_color

        for x1, y1 in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if x1 < 0 or x1 >= w or y1 < 0 or y1 >= h:
                continue
            if comp[y1][x1] == 0:
                assign_component(x1, y1, comp_idx, ref, preview_color)
    

    def find_border(x0, y0):
        ref = arr[y][x]
        taken = np.zeros((h, w))
        border = []

        def find_border_dfs(x, y, x1, y1):
            border.append((x, y))
            taken[y][x] = 1
            found = False
            pos = len(border)
            
            for x2, y2 in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if x2 == x1 and y2 == y1:
                    continue
                # this solves the problem of (x0, y0) being covered on 3 sides
                if dist_2d((x0, y0), (x2, y2)) <= 2 and dist_2d((x0, y0), (x, y)) > 2:
                    return True
                if taken[y2][x2] == 1 or not is_in_border(x2, y2, ref):
                    continue

                # if the search got stuck, try again
                if found and len(border) - pos <= 8:
                    while len(border) > pos:
                        x3, y3 = border.pop()
                        taken[y3][x3] = 0
                elif found and DEBUG:
                    print("[DEBUG] Stuck at", x, y)
                    break
                found = True

                # if (x1, y1), (x, y), (x2, y2) are aligned, remove (x, y)
                if (y2 - y) * (x - x1) == (y - y1) * (x2 - x):
                    border.pop()
                if find_border_dfs(x2, y2, x, y):
                    return True
            
            return False
        
        find_border_dfs(x0, y0, -1, -1)
        
        # if there are multiple nodes within RESOLUTION distance,
        # only keep one
        new_border = []
        for node in border:
            if len(new_border) != 0 and dist_2d(new_border[-1], node) <= RESOLUTION:
                continue
            new_border.append(node)
        
        # if three consecutive nodes are aligned enough, remove the middle one
        # at each step, remove the most aligned
        # (this could be done much faster)
        while True:
            min_ratio = TRESHOLD
            min_node = -1

            if len(new_border) < 3:
                break

            for idx in range(0, len(new_border)):
                x0, y0 = new_border[(idx - 1 + len(new_border)) % len(new_border)]
                x1, y1 = new_border[idx]
                x2, y2 = new_border[(idx + 1) % len(new_border)]

                a = y2 - y0
                b = x0 - x2
                c = y0 * (x2 - x0) - x0 * (y2 - y0)

                d = a * x1 + b * y1 + c
                distance = d ** 2 / (a ** 2 + b ** 2)
                length = min((x1 - x0) ** 2 + (y1 - y0) ** 2, (x1 - x2) ** 2 + (y1 - y2) ** 2)
                ratio = distance / min(length, COLLAPSE)

                if ratio < min_ratio:
                    min_ratio = ratio
                    min_node = idx

            if min_ratio < TRESHOLD:
                new_border.pop(min_node)
            else:
                break

        for p in new_border:
            highlight(p)
        
        return new_border
    

    # the center is computed just as the average of the maximum and minimum
    # x and y values
    def find_center(border):
        xvals = [x for x, y in border]
        yvals = [y for x, y in border]
        
        center = (
            floor((max(xvals) + min(xvals)) / 2),
            floor((max(yvals) + min(yvals)) / 2)
        )
        highlight(center)
        return center


    json_data = []
    cur_comp = 1

    for x in range(0, w):
        for y in range(0, h):
            if comp[y][x] != 0:
                continue

            preview_color = (
                randint(0, 255),
                randint(0, 255),
                randint(0, 255)
            )
            assign_component(x, y, cur_comp, arr[y][x], preview_color)

            if cur_comp > 1:
                border = find_border(x, y)
                json_data.append({
                    "id": cur_comp,
                    "type": "default",
                    "label": f"Component {cur_comp}",
                    "color": "auto",
                    "center": find_center(border),
                    "border": border,
                })
                print("[NEW CC]", cur_comp)

            cur_comp += 1
    
    print("[SUCCESS] Found", cur_comp - 1, "CCs")

    with open("output.json", "w") as output:
        json.dump({
            "width": w,
            "height": h,
            "components": json_data
        }, output)

    preview = Image.fromarray(preview_data)
    preview.show()


if __name__ == "__main__":
    with Image.open(sys.argv[1]) as img:
        trace_png(np.asarray(img))
