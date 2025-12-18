import drawsvg as draw
import cairosvg
from lib import from_names, make_graph, split_into_tiles


def save_as_pdf(img, path):
    svg_bytes = img.as_svg().encode("utf-8")
    cairosvg.svg2pdf(bytestring=svg_bytes, write_to=path)


def polyband():
    instruments = from_names(
        [
            "voice/mezzosoprano",
            "insts/fl",
            "insts/cl",
            "insts/as",
            "insts/ts",
            "insts/bs",
            "insts/tp",
            "insts/tb",
            "insts/btb",
            "insts/pn",
            "insts/git",
            "insts/b",
        ]
    )

    content, content_format = make_graph("Polyband Ranges", instruments)
    img = draw.Drawing(*content_format)

    img.append(content)
    save_as_pdf(img, "out/polyband.pdf")

    tiles = split_into_tiles(content, content_format)
    for tile, (x, y) in tiles:
        name = f"out/polyband_{x}_{y}.pdf"
        save_as_pdf(tile, name)


def choir():
    instruments = from_names(
        [
            "voice/soprano",
            "voice/mezzosoprano",
            "voice/alto",
            "voice/tenor",
            "voice/baritone",
            "voice/bass",
        ]
    )

    content, content_format = make_graph("Choir Ranges", instruments)
    img = draw.Drawing(*content_format)

    img.append(content)
    save_as_pdf(img, "out/choir.pdf")


if __name__ == "__main__":
    polyband()
    choir()
