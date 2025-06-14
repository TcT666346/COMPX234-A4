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