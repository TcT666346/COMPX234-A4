import socket
import sys
import base64
import os

def reliable_send_receive(sock, dest_addr, message, timeout=1.0, max_retries=5):
    """带超时重传机制的可靠发送接收函数"""
    retries = 0
    current_timeout = timeout
    
    while retries < max_retries:
        try:
            sock.settimeout(current_timeout)
            sock.sendto(message.encode(), dest_addr)
            response, _ = sock.recvfrom(2048)
            return response.decode().strip()
        except socket.timeout:
            retries += 1
            current_timeout *= 2
            print(f"Timeout, retrying ({retries}/{max_retries})...")
    
    raise Exception("No response after maximum retries")

def download_file(sock, server_host, data_port, filename, file_size):
    """下载单个文件的核心逻辑"""
    with open(filename, 'wb') as f:
        downloaded = 0
        block_size = 1000  # 每个数据块的大小
        
        while downloaded < file_size:
            end = min(downloaded + block_size - 1, file_size - 1)
            request = f"FILE {filename} GET START {downloaded} END {end}"
            
            try:
                response = reliable_send_receive(
                    sock, 
                    (server_host, data_port), 
                    request
                )
            except Exception as e:
                print(f"Download failed: {str(e)}")
                return False
            
            # 解析响应
            parts = response.split()
            if len(parts) < 8 or parts[0] != "FILE" or parts[2] != "OK":
                print("Invalid response format")
                return False
            
            # 处理数据
            data_index = response.find("DATA ") + 5
            base64_data = response[data_index:]
            binary_data = base64.b64decode(base64_data)
            f.write(binary_data)
            downloaded += len(binary_data)
            print('*', end='', flush=True)
        
        print(f"\nDownloaded {downloaded} bytes")

     # 发送关闭请求
    close_msg = f"FILE {filename} CLOSE"
    try:
        response = reliable_send_receive(
            sock, 
            (server_host, data_port), 
            close_msg
        )
        if response != f"FILE {filename} CLOSE_OK":
            print("Close confirmation error")
    except Exception as e:
        print(f"Close failed: {str(e)}")
    
    return True

def main():
    if len(sys.argv) != 4:
        print("Usage: python UDPclient.py <host> <port> <filelist>")
        return
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    filelist = sys.argv[3]
    
    # 读取文件列表
    try:
        with open(filelist, 'r') as f:
            files = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"File list {filelist} not found")
        return
    
    # 创建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for filename in files:
        print(f"\nRequesting {filename}...")
        
        # 发送下载请求
        download_request = f"DOWNLOAD {filename}"
        try:
            response = reliable_send_receive(sock, (host, port), download_request)
        except Exception as e:
            print(f"Request failed: {str(e)}")
            continue
        
        # 处理响应
        parts = response.split()
        if parts[0] == "ERR":
            print(f"Error: {response}")
            continue
        
        if len(parts) < 6 or parts[0] != "OK" or parts[2] != "SIZE" or parts[4] != "PORT":
            print(f"Invalid response: {response}")
            continue
        
        try:
            file_size = int(parts[3])
            data_port = int(parts[5])
            print(f"File size: {file_size} bytes, Data port: {data_port}")
        except ValueError:
            print("Invalid size/port format")
            continue
        
        # 开始下载文件
        print(f"Downloading {filename}...")
        if download_file(sock, host, data_port, filename, file_size):
            print(f"Successfully downloaded {filename}")
    
    sock.close()

if __name__ == "__main__":
    main()    