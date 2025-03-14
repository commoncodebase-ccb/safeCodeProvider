import os
import sys
import ctypes
import time
import platform

def get_pid_by_port(port):
    """Verilen portu kullanan işlemin PID'sini döndürür (Windows, MacOS ve Linux için)"""
    try:
        if platform.system() == "Windows":
            result = os.popen(f'netstat -ano | findstr :{port}').read()
        else:  # MacOS & Linux
            result = os.popen(f"lsof -i :{port} | grep LISTEN").read()
        
        if result:
            lines = result.strip().split("\n")
            for line in lines:
                parts = line.split()
                if platform.system() == "Windows":
                    if len(parts) >= 5 and parts[1].endswith(f':{port}'):
                        return parts[-1]  # Windows için PID en sağda
                else:
                    if parts[1].isdigit():
                        return parts[1]  # MacOS & Linux için PID ikinci sütunda
        return None
    except Exception as e:
        print(f"⚠️ PID bulunurken hata oluştu: {e}")
        return None

def is_admin():
    """Programın yönetici yetkisiyle çalışıp çalışmadığını kontrol eder"""
    if platform.system() == "Windows":
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        return os.geteuid() == 0  # MacOS & Linux için root yetkisi kontrolü

def request_admin():
    """Eğer yönetici izni yoksa, programı yönetici olarak yeniden başlatır"""
    if not is_admin():
        print("🔄 Yönetici yetkisi gerekiyor, tekrar başlatılıyor...")
        if platform.system() == "Windows":
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)  # MacOS & Linux için sudo kullan
        sys.exit()

def close_port(port):
    try:
        request_admin()  # Yönetici olarak çalıştırmayı kontrol et

        pid = get_pid_by_port(port)
        if pid:
            print(f"⚠️ Port {port} kullanılıyor. PID: {pid} - Kapatılıyor...")
            if platform.system() == "Windows":
                os.system(f"taskkill /PID {pid} /F > nul 2>&1")  # Windows için
            else:
                os.system(f"kill -9 {pid}")  # MacOS & Linux için
            time.sleep(1)
            print(f"✅ {port} portu başarıyla kapatıldı!")
        else:
            print(f"ℹ️ {port} portunu kullanan bir işlem bulunamadı. Firewall üzerinden engelleniyor...")
            if platform.system() == "Windows":
                os.system(f'netsh advfirewall firewall add rule name="Block_{port}" dir=in action=block protocol=TCP localport={port} > nul 2>&1')
            else:
                os.system(f"sudo iptables -A INPUT -p tcp --dport {port} -j DROP")  # Linux için
                os.system(f"sudo ufw deny {port}")  # Alternatif olarak Ubuntu UFW kullanımı
                os.system(f'echo "block in proto tcp from any to any port {port}" | sudo pfctl -ef -')  # MacOS için
            print(f"✅ {port} portu firewall üzerinden engellendi!")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    close_port(8001)


