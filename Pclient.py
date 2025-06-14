import socket
import sys
import base64
import os

def handle_file_transmission(client_addr, filename, file_size):
    """处理单个文件传输的线程函数"""
    # 创建新的UDP套接字
    data_port = random.randint(50000, 51000)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        data_sock.bind(('', data_port))
        print(f"Data socket bound to port {data_port}")
    except:
        print(f"Port {data_port} busy, aborting")
        return
    
    try:
        # 发送OK响应（通过主套接字）
        main_sock.sendto(f"OK {filename} SIZE {file_size} PORT {data_port}".encode(), client_addr)
        
        with open(filename, 'rb') as f:
            while True:
                # 等待客户端请求
                data, addr = data_sock.recvfrom(1024)
                message = data.decode().strip()
                parts = message.split()
                
                # 处理关闭请求
                if len(parts) >= 3 and parts[0] == "FILE" and parts[2] == "CLOSE":
                    data_sock.sendto(f"FILE {filename} CLOSE_OK".encode(), addr)
                    print(f"Closed connection for {filename}")
                    break
                
                # 处理数据请求
                if len(parts) < 7 or parts[0] != "FILE" or parts[2] != "GET":
                    continue
                
                try:
                    start = int(parts[4])
                    end = int(parts[6])
                    block_size = end - start + 1
                    
                    # 读取文件数据
                    f.seek(start)
                    file_data = f.read(block_size)
                    
                    # 编码并发送数据
                    base64_data = base64.b64encode(file_data).decode()
                    response = f"FILE {filename} OK START {start} END {end} DATA {base64_data}"
                    data_sock.sendto(response.encode(), addr)
                except Exception as e:
                    print(f"Error handling request: {str(e)}")
    finally:
        data_sock.close()


# 全局变量（主套接字）
main_sock = None

def main():
    global main_sock
    
    if len(sys.argv) != 2:
        print("Usage: python UDPserver.py <port>")
        return
    
    port = int(sys.argv[1])
    
    # 创建主UDP套接字
    main_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    main_sock.bind(('', port))
    print(f"Server listening on port {port}")
    
    while True:
        try:
            # 等待下载请求
            data, addr = main_sock.recvfrom(1024)
            message = data.decode().strip()
            parts = message.split()
            
            if len(parts) < 2 or parts[0] != "DOWNLOAD":
                continue
            
            filename = parts[1]
            print(f"Received DOWNLOAD request for {filename} from {addr}")
            
            # 检查文件是否存在
            if not os.path.exists(filename):
                main_sock.sendto(f"ERR {filename} NOT_FOUND".encode(), addr)
                print(f"File {filename} not found")
                continue
            
            # 获取文件大小
            file_size = os.path.getsize(filename)
            
            # 创建新线程处理文件传输
            threading.Thread(
                target=handle_file_transmission,
                args=(addr, filename, file_size)
            ).start()
            
        except KeyboardInterrupt:
            print("\nServer shutting down...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
    
    main_sock.close()

if __name__ == "__main__":
    main()