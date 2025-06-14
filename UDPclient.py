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