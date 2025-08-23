import json
from random import randint
import sys

colors = ["red", "green", "blue", "grey", "orange", "brown", "darkblue", "darkgreen", "darkred", "violet"]

def create_svg(data):
    with open("output.svg", "w") as output:
        output.write(
            f'<svg height="{data["height"]}" width="{data["width"]}" xmlns="http://www.w3.org/2000/svg">'
        )

        for path in data["components"]:
            description = " L ".join([
                f"{node[0]} {node[1]}" for node in path["border"]
            ])

            color = path["color"]
            if color == "auto":
                color = colors[randint(0, len(colors) - 1)]

            output.write(
                f'<path d="M {description} Z" style="fill:{color}" />'
            )
            output.write(
                f'''
                <text
                    x="{path["center"][0]}"
                    y="{path["center"][1]}"
                    fill="white"
                    font-size="35"
                    font-weight="bold"
                    dominant-baseline="middle"
                    text-anchor="middle"
                >
                    {path["label"]}
                </text>
                '''
            )

        output.write("</svg>")

if __name__ == "__main__":
    with open(sys.argv[1], "r") as input_file:
        create_svg(json.load(input_file))
