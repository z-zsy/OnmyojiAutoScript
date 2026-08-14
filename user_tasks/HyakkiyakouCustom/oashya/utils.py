import cv2
import numpy as np

from .labels import id2label
from .labels import sp, ssr, sr, r, n, g

palettes = np.random.uniform(0, 255, size=(226, 3))


def draw_tracks(image, tracks):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    for _id, _class, _conf, _cx, _cy, _w, _h, _v in tracks:
        x1 = int(_cx - _w / 2)
        y1 = int(_cy - _h / 2)
        x2 = int(_cx + _w / 2)
        y2 = int(_cy + _h / 2)
        text_label = f'{id2label(_class)}({_conf:.2f})'
        text_id = f'ID: {_id}'

        color = palettes[_class]
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 1)
        (text_width, text_height), baseline = cv2.getTextSize(text_label,
                                                              fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                                              fontScale=0.5,
                                                              thickness=1)
        bottom_left_corner = (x1, y1)
        top_right_corner = (x1 + text_width, y1 + text_height + baseline)
        cv2.rectangle(image, bottom_left_corner, top_right_corner, color, cv2.FILLED)
        cv2.putText(image,
                    text_label,
                    (x1, y1 + text_height),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.5,
                    color=(255, 255, 255),
                    thickness=1)
        cv2.putText(image,
                    text_id,
                    (x1, y1 - text_height + baseline),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.5,
                    color=color,
                    thickness=1)
    text_oas: str = 'Built' + ' ' + 'with' + ' OAS'
    text_open: str = 'Open ' + 'Source'
    cv2.putText(image,
                text_open,
                (40, 70),
                fontFace=cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                fontScale=1.5,
                color=(0, 255, 0),
                thickness=2)
    cv2.putText(image,
                text_oas,
                (800, 650),
                fontFace=cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                fontScale=2,
                color=(0, 255, 0),
                thickness=2)
    return image


def generate_markdown_table(data, headers=None):
    if headers:
        markdown_table = "| " + " | ".join(headers) + " |\n"
        markdown_table += "|-----" * len(headers) + "|\n"
    else:
        markdown_table = ""

    for row in data:
        markdown_table += '|'
        for value in row:
            markdown_table += f' {value} |'
        markdown_table += '\n'

    return markdown_table


def generate_class_table1():
    markdown_table = ''
    markdown_table += '| Label | Name | Label | Name |\n'
    markdown_table += "|-----" * 4 + "|\n"
    sp_label = list(sp.keys())
    sp_name = list(sp.values())
    ssr_label = list(ssr.keys())
    ssr_name = list(ssr.values())
    for index in range(max(len(sp_label), len(ssr_label))):
        if index < len(sp_label):
            markdown_table += f'| {sp_label[index]} | {sp_name[index]}'
        else:
            markdown_table += '|  |'
        if index < len(ssr_label):
            markdown_table += f' | {ssr_label[index]} | {ssr_name[index]}'
        else:
            markdown_table += '|  |  '
        markdown_table += '|\n'
    return markdown_table

def generate_class_table2():
    markdown_table = ''
    markdown_table += '| Label | Name | Label | Name |\n'
    markdown_table += "|-----" * 4 + "|\n"
    sr_label = list(sr.keys())
    sr_name = list(sr.values())
    r_label = list(r.keys())
    r_name = list(r.values())
    n_label = list(n.keys())
    n_name = list(n.values())
    g_label = list(g.keys())
    g_name = list(g.values())
    row1 = sr_label
    row2 = sr_name
    row3 = r_label + n_label + g_label
    row4 = r_name + n_name + g_name
    for index in range(max(len(row1), len(row3))):
        if index < len(row1):
            markdown_table += f'| {row1[index]} | {row2[index]}'
        else:
            markdown_table += '|  |  '
        if index < len(row3):
            markdown_table += f' | {row3[index]} | {row4[index]}'
        else:
            markdown_table += '|  |  '
        markdown_table += '|\n'
    return markdown_table

def generate_class_table():
    markdown_table = ''
    markdown_table += '| Label | Name | Label | Name | Label | Name | Label | Name|\n'
    markdown_table += "|-----" * 8 + "|\n"
    sp_label = list(sp.keys())
    sp_name = list(sp.values())
    ssr_label = list(ssr.keys())
    ssr_name = list(ssr.values())
    sr_label = list(sr.keys())
    sr_name = list(sr.values())
    r_label = list(r.keys())
    r_name = list(r.values())
    n_label = list(n.keys())
    n_name = list(n.values())
    g_label = list(g.keys())
    g_name = list(g.values())
    row1 = sp_label
    row2 = sp_name
    row3 = ssr_label
    row4 = ssr_name
    row5 = sr_label
    row6 = sr_name
    row7 = r_label + n_label + g_label
    row8 = r_name + n_name + g_name
    for index in range(max(len(row1), len(row3), len(row5), len(row7))):
        if index < len(row1):
            markdown_table += f'| {row1[index]} | {row2[index]}'
        else:
            markdown_table += '|  |  '
        if index < len(row3):
            markdown_table += f' | {row3[index]} | {row4[index]}'
        else:
            markdown_table += ' |  |  '
        if index < len(row5):
            markdown_table += f' | {row5[index]} | {row6[index]}'
        else:
            markdown_table += ' |  |  '
        if index < len(row7):
            markdown_table += f' | {row7[index]} | {row8[index]}'
        else:
            markdown_table += ' |  |  '
        markdown_table += ' |\n'
    return markdown_table
