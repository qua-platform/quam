from quam.components.channels import Channel


def test_channel_frame_rotation_2pi(mocker):
    mocker.patch("qm.qua.frame_rotation_2pi")

    channel = Channel(id="channel")

    channel.frame_rotation_2pi(0.5)

    import qm.qua

    qm.qua.frame_rotation_2pi.assert_called_once_with(0.5, "channel")


def test_channel_update_frequency(mocker):
    mocker.patch("qm.qua.update_frequency")

    channel = Channel(id="channel")

    channel.update_frequency(100e6)

    import qm.qua

    qm.qua.update_frequency.assert_called_once_with("channel", 100e6, "Hz", False)
