'''utilities to help blend in the pyxb generated code'''


def get_tag(element, name: str):
    # pylint: disable=protected-access
    for key, value in element._ElementMap.items():
        if key.localName() == name:
            return getattr(element, value.id())
    return None
