#!/usr/bin/python3
from argparse import ArgumentParser
from utils.audio_source import AudioStream
from utils.mic_source import MicrophoneStream
from service.dictation_settings import DictationSettings
from service.streaming_recognizer import StreamingRecognizer
from VERSION import DICTATION_CLIENT_VERSION


def print_results(results):
    print("\n=====")
    for alternatives in results:
        if not isinstance(alternatives, list):
            alternatives = [alternatives]
        if alternatives[0]['transcript'] != '':  # ignore empty recognitions
            for res in alternatives:
                print("\n{}".format(res['transcript']))
                words = res['transcript'].split()
                ali = res['alignment']
                if len(words) == len(ali):
                    for i in range(0, len(words)):
                        time = ali[i]
                        if len(time) > 0:
                            print("{} [{}.{:02d} - {}.{:02d}]".format(words[i], time[0].seconds, int(time[0].nanos / 10000000),
                                                                  time[1].seconds, int(time[1].nanos / 10000000)))
            print("\n=====")


def create_audio_stream(args):
    # create wave file stream
    if args.wave is not None:
        return AudioStream(args.wave)

    # create microphone stream
    if args.mic:
        rate = 16000  # [Hz]
        chunk = int(rate / 10)  # [100 ms]
        return MicrophoneStream(rate, chunk)

    # default
    raise ValueError("Unknown media source to create")


if __name__ == '__main__':
    print("Dictation ASR gRPC client " + DICTATION_CLIENT_VERSION)

    parser = ArgumentParser()
    parser.add_argument("--service-address", dest="address", required=True,
                        help="IP address and port (address:port) of a service the client will connect to.", type=str)
    parser.add_argument("--wave-path", dest="wave",
                        help="Path to wave file with speech to be recognized. Should be mono, 8kHz or 16kHz.")
    parser.add_argument("--mic", help="Use microphone as an audio source (instead of wave file).", action='store_true')
    parser.add_argument("--session-id",
                        help="Session ID to be passed to the service. If not specified, the service will generate a default session ID itself.",
                        default="", type=str)
    parser.add_argument("--grpc-timeout",
                        help="Timeout in milliseconds used to set gRPC deadline - how long the client is willing to wait for a reply from the server. If not specified, the service will set the deadline to a very large number.",
                        default=0, type=int)
    # request configuration section
    parser.add_argument("--max-alternatives", help="Maximum number of recognition hypotheses to be returned.",
                        default=1, type=int)
    parser.add_argument("--time-offsets", help="If set - the recognizer will return also word time offsets.",
                        action="store_true", default=False)
    parser.add_argument("--single-utterance", help="If set - the recognizer will detect a single spoken utterance.",
                        action="store_true", default=False)
    parser.add_argument("--interim-results", help="If set - messages with temporal results will be shown.",
                        action="store_true", default=False)
    # timeouts
    parser.add_argument("--no-input-timeout", help="MRCP v2 no input timeout [ms].", default=5000, type=int)
    parser.add_argument("--speech-complete-timeout", help="MRCP v2 speech complete timeout [ms].", default=2000,
                        type=int)
    parser.add_argument("--speech-incomplete-timeout", help="MRCP v2 speech incomplete timeout [ms].", default=4000,
                        type=int)
    parser.add_argument("--recognition-timeout", help="MRCP v2 recognition timeout [ms].", default=10000, type=int)

    # Stream audio to the ASR engine and print all hypotheses to standard output
    args = parser.parse_args()

    if args.wave is not None or args.mic:
        with create_audio_stream(args) as stream:
            settings = DictationSettings(args)
            recognizer = StreamingRecognizer(args.address, settings)

            print('Recognizing...')
            results = recognizer.recognize(stream)
            print_results(results)
