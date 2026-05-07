import sys

def calibrate():
    """
    Calibrate the camera of the first Emio camera found
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
    Start a UDP bridge configured with the parameters found in params
    """
    import emioapi.udp_bridge.udp_bridge as udpBdrige
    config = udpBdrige.UDPBridgeConfig(args.fps,
                                args.nb_markers,
                                args.side,
                                args.sort,
                                args.remote_ip,
                                args.remote_port,
                                args.local_port,
                                args.bind_port,
                                args.recv_timeout)
    
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


    # --- Subparser for 'startUDP' command ---
    parser_udp = subparsers.add_parser("startUDP", help="Start a UDP bridge for motor/camera data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Add the specific arguments needed for startUDP here
    parser_udp.add_argument("--fps",       type=int, default=prm.fps, help="Frames per second (e.g., 30)")
    parser_udp.add_argument("--nb_markers",  type=int, default=prm.nb_markers, help="Number of markers to process")
    parser_udp.add_argument("--side",       choices=["top", "front", "plan"], default=prm.side, help="Camera side view")
    parser_udp.add_argument("--sort",        choices=["y", "z"], default=prm.sort, help="Sorting axis")
    parser_udp.add_argument("--remote_ip",    type=str, default=prm.remote_ip, help="Remote IP address")
    parser_udp.add_argument("--remote_port",  type=int, default=prm.remote_port, help="Remote Port")
    parser_udp.add_argument("--local_port",    type=int, default=prm.local_port, help="Local Port")
    parser_udp.add_argument("--bind_port",      type=int, default=prm.bind_port, help="Bind port for local communication")
    parser_udp.add_argument("--recv_timeout",  type=float, default=prm.recv_timeout, help="Receive timeout in seconds")

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