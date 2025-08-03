## Windows 
 
   - Download 3rd Party XServer for Windows from https://sourceforge.net/projects/vcxsrv/
   - Install this 3rd Party XServer for Windows  
   - Launch this 3rd Party XServer for Windows and follow default configuration, you can probably configure it to display on new window or use one large window (black screen should appear)   
   - Set DISPLAY variable to point on your local windows ip address: host.docker.internal:0
   - Launch docker image or docker compose configured in this way and content should appear there

# more information: https://www.youtube.com/watch?v=UEre6Bd75dw

# other way is to install local Ubuntu on Windows using docker
	- Install WSL extension
	- Run in command line: wsl --install -d Ubuntu  
	- Enable installed Ubuntu in previous step
	- Mount Ubuntu X Server volume in docker compose or using -v in Dockerfile
	- Specify DEVICE environment variable
# Original choregraphe images and documentation 
   - https://hub.docker.com/r/fero/choregraphe  
   - https://hub.docker.com/r/alvimpaulo/choregraphe (newer)

This image runs on x86_64 systems. After you have pulled the image, run choregraphe with the command:  

docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix choregraphe:2.1.4  

Please note that the first /tmp/.X11-unix represent the directory of Ubuntu X server sockets change it accordingly to your OS if different!  

# Docker compose configuration:  

choregraphe288:  
        image: alvimpaulo/choregraphe:2.8.6  
        environment:  
            DISPLAY: host.docker.internal:0  
        ports:  
            - "127.0.0.1:9559:9559"  
        depends_on:  
            volumeCopyInit:  
                condition: service_completed_successfully  
        networks:  
            - buildernet  

not working:  

choregraphe288:
        image: alvimpaulo/choregraphe:2.8.6
        environment:
            DISPLAY: :0
        ports:
            - "127.0.0.1:9559:9559"
        volumes:
            - \\wsl.localhost\Ubuntu\mnt\wslg:\tmp
        depends_on:
            volumeCopyInit:
                condition: service_completed_successfully 
        networks:
            - buildernet

choregraphe288:
        image: alvimpaulo/choregraphe:2.8.6
        environment:
            DISPLAY: :0
            PULSE_SERVER: /tmp/PulseServer
        ports:
            - "127.0.0.1:9559:9559"
        volumes:
            - type: bind
              source: //wsl.localhost/Ubuntu/tmp/.X11-unix
              target: /tmp/.X11-unix
        depends_on:
            volumeCopyInit:
                condition: service_completed_successfully 
        networks:
            - buildernet

