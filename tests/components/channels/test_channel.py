from quam.components.channels import Channel


def test_channel_frame_rotation_2pi(mocker):
    mocker.patch("quam.components.channels.frame_rotation_2pi")

    channel = Channel(id="channel")

    channel.frame_rotation_2pi(0.5)

    from quam.components.channels import frame_rotation_2pi

    frame_rotation_2pi.assert_called_once_with(0.5, "channel")
