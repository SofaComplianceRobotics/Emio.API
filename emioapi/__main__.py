import sys

def calibrate():
    """
    Calibrate the camera of the first Emio camera found. For more informations about the calibration process, please refer to the EmioCamera.calibrate() method documentation.
    """
    import emioapi
    from emioapi._logging_config import logger 

    camera = emioapi.EmioCamera(show=True)
    print("Available cameras:", emioapi.EmioCamera.listCameras())

    if camera.open():
        print(f"Camera {camera.camera_serial} opened.")
        if camera.calibration_status == emioapi.CalibrationStatusEnum.NOT_CALIBRATED:
            camera.calibrate()
        else:
            print("Camera is already calibrated.")

        while camera.is_running:
            try:
                camera.update() # update the camera frame and trackers
                logger.info(camera.trackers_pos)
            except KeyboardInterrupt: 
                logger.info("Keyboard interrupt received.")
                break
            except Exception as e:
                logger.exception(f"Error during communication: {e}")
                break

        camera.close()
    else:
        print("Failed to open camera.")

def startUDP(args):
    """
    Start a UDP bridge configured with the parameters found in args. 

    A handshake is done at the beginning to ensure that the remote host is ready to receive data. It should follow the same protocol describded below with dummy data.

    The sequence number is a simple counter that is incremented at each frame. It is used by the process_motors process to make sure that the remote is synchronized.
    
    The protocol is as follows:
    - The bridge sends a packet made of a sequence number, the four motors positions and followed by the marker(s) position(s) (x, y, z)
    - The remote host should reply with a packet containing the four motors positions to send to the Emio robot.

    """
    import emioapi.udp_bridge.udp_bridge as udpBdrige
    config = udpBdrige.UDPBridgeConfig(
        fps = args.fps,
        nb_markers = args.nb_markers,
        side = args.side,
        sort = args.sort,
        remote_ip = args.remote_ip,
        remote_port = args.remote_port,
        local_port = args.local_port,
        bind_port = args.bind_port,
        recv_timeout = args.recv_timeout,
        camera_only = args.camera_only,
        motors_only = args.motors_only
    )

    print("-"*50)
    print(f"Starting UDP bridge with config: {config}")
    print("-"*50)
    
    udpBdrige.startUDPbridge(config)


def parse_args():
    
    import argparse
    import emioapi.udp_bridge.udp_bridge_params as prm

    p = argparse.ArgumentParser(
        description="Emio API tools for Emio",
        prog="emioapi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = p.add_subparsers(
        title="Available Commands", 
        dest="command", 
        required=True
    )

    # --- Subparser for 'calibrate' command ---
    parser_calibrate = subparsers.add_parser("calibrate", help="Calibrate the Emio camera.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_calibrate.description = calibrate.__doc__


    # --- Subparser for 'startUDP' command ---
    parser_udp = subparsers.add_parser("startUDP", help="Start a UDP bridge for motor/camera data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser_udp.description = startUDP.__doc__
    
    # Add the specific arguments needed for startUDP here
    parser_udp.add_argument("--fps",       type=int, default=prm.fps, help="Frames per second (e.g., 30)")
    parser_udp.add_argument("--nb-markers",  type=int, default=prm.nb_markers, help="Number of markers to process")
    parser_udp.add_argument("--side",       choices=["top", "front", "plane"], default=prm.side, help="Camera side view")
    parser_udp.add_argument("--sort",        choices=["y", "z"], default=prm.sort, help="Sorting axis")
    parser_udp.add_argument("--remote-ip",    type=str, default=prm.remote_ip, help="Remote IP address")
    parser_udp.add_argument("--remote-port",  type=int, default=prm.remote_port, help="Remote Port")
    parser_udp.add_argument("--local-port",    type=int, default=prm.local_port, help="Local Port")
    parser_udp.add_argument("--bind-port",      type=int, default=prm.bind_port, help="Bind port for local communication")
    parser_udp.add_argument("--recv-timeout",  type=float, default=prm.recv_timeout, help="Receive timeout in seconds")
    parser_udp.add_argument("--camera-only",  action=argparse.BooleanOptionalAction, default=False, help="Only send the markers position without waiting for the motors command. The motors positions will be sent as 0. And no command will be applied to the motors.")
    parser_udp.add_argument("--motors-only",  action=argparse.BooleanOptionalAction, default=False, help="Only send the motors position without waiting for the camera data")

    try:
        # Parse the arguments
        args = p.parse_args()
        
        print(f"Command chosen: {args.command}" + (f" with parameters: {vars(args)}" if args.command == "startUDP" else ""))

        # Execute the function associated with the chosen command
        if args.command == "calibrate":
            calibrate()
        elif args.command == "startUDP":
            startUDP(args)
        else:
            print(f"Unknown command: {args.command}")
    except:
        p.print_help()
        print()
        parser_calibrate.print_help()
        print()
        parser_udp.print_help()
        pass


if __name__ == "__main__":
    try:
        args = parse_args()
    except Exception as e:
        import traceback
        print(f"An error happened: {traceback.format_exc()}")