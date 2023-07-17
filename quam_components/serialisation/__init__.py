def get_serialiser(filepath):
    from quam_components.serialisation.json import JSONSerialiser

    # TODO implement better logic to discriminate serialiser
    return JSONSerialiser()
