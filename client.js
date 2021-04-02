// peer connection
var pc = null;

var localStream;

function createPeerConnection() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    // config.iceServers = [{urls: ['stun:stun.l.google.com:19302']}];

    pc = new RTCPeerConnection(config);

    return pc;
}

function negotiate() {
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription;

        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
                video_transform: "none",
                user_id: "test_id" /* ИД пользователя */
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function(response) {
        return response.json();
    }).then(function(answer) {
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}

function start() {
    document.getElementById('start').style.display = 'none';

    pc = createPeerConnection();

    var constraints = {
        audio: true,
        video: { width: 640, height: 480 }
    };

    navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
        stream.getTracks().forEach(function(track) {
            pc.addTrack(track, stream);
        });
        var video = document.getElementById('video');
        video.srcObject = stream;
        localStream = stream;
        video.muted = true;
        return negotiate();
    }, function(err) {
        alert('Could not acquire media: ' + err);
    });

    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    document.getElementById('stop').style.display = 'none';
    document.getElementById('start').style.display = 'inline-block';

    localStream.getTracks().forEach(function(track) {
        track.stop();
    });
    var video = document.querySelector('video');
    video.pause();
    video.srcObject = null;

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function(transceiver) {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // close local audio / video
    pc.getSenders().forEach(function(sender) {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}
