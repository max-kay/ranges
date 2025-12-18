def parse(path: str) -> tuple[str, dict[str, list[str]]]:
    with open(path, encoding="utf8", mode="r") as file:
        lines = []
        for line in file.readlines():
            line, *_ = line.strip().split("//")
            line = line.strip()
            if line:
                lines.append(line)
    return __parse_lines(lines, path=path)


def parse_str(string: str) -> tuple[str, dict[str, list[str]]]:
    lines = string.splitlines()
    return __parse_lines(lines)


def __parse_lines(lines: list[str], /, path=None) -> tuple[str, dict[str, list[str]]]:
    name = lines[0]
    active_section: str | None = None
    section_list: list[str] = []
    out_dict: dict[str, list[str]] = {}
    for line in lines[1:]:
        if ":" in line:
            if active_section:
                out_dict[active_section] = section_list
                active_section = None
                section_list = []
            section_title, *more = line.split(":")
            more = [v.strip() for v in more if v.strip() != ""]
            if len(more) == 0:
                active_section = section_title.lower()
            if len(more) == 1:
                out_dict[section_title.lower()] = [
                    seg.strip() for seg in more[0].split() if seg.strip() != ""
                ]
            if len(more) > 1:
                if path:
                    raise ValueError(f"invalid line in file {path}\n{line}")
                else:
                    raise ValueError(f"invalid line: \n{line}")
        else:
            if not active_section:
                print("active", active_section)
                if path:
                    raise ValueError(
                        f"found value before section title in file {path} line:\n{line}"
                    )
                else:
                    raise ValueError(f"found value before section title line:\n{line}")
            section_list.append(line)
    else:
        if active_section:
            out_dict[active_section] = section_list
    return (name, out_dict)
