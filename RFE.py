import os,platform,cmd
try:
    import paramiko
    from cryptography.fernet import Fernet
    from tinydb import TinyDB,Query
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
except:
    if platform.system()=="Windows":
        os.system("pip install paramiko==3.4.0 cryptography==42.0.5 tinydb==4.8.0 prompt-toolkit==3.0.43")
    else:
        os.system("pip3 install paramiko==3.4.0 cryptography==42.0.5 tinydb==4.8.0 prompt-toolkit==3.0.43")
    import paramiko
    from cryptography.fernet import Fernet
    from tinydb import TinyDB,Query
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter

db = TinyDB('records.json')
DB_search=Query()
#word Sugesstions
command_suggestions={"ls","cd","pwd","ftp_edit-","ftp_update","ftp_push","ftp_get","exit","close"}
#Commads
class BaseClase:
    def __init__(self,host,username,port=22,password=None) -> None:
        self.serverip=host
        self.password=password
        self.port=port
        self.user=username
        self.currnet_location=None
        self.client = paramiko.SSHClient()
        self.SSH=False
        self.FTP=False
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    def Connect_SSH(self):
        """Will Use To Connect With The Server Via SSH"""
        try:
            if self.password:
                self.client.connect(self.serverip, port=self.port, username=self.user,password=self.password)
            else:
                self.client.connect(self.serverip, port=self.port, username=self.user)    
            self.SSH=True
        except:
            print("Unable To connect SSH !")
            exit()
    def Connect_FTP(self):
        """Will Use To Connect With The Server Via FTP"""
        try:
            self.ftp = self.client.open_sftp()
            self.FTP=True
        except:
            print("Unable To Connect FTP!") 
    def StoreEditInfo(self,server_location,file):
        """Will Use To Store File Info In Edit Mood FTP"""
        key = Fernet.generate_key()
        message = f"{self.serverip}>>{os.getcwd()}>>{server_location}>>{file}"
        encrypted_message = Fernet(key).encrypt(message.encode())
        with open(".info","w") as f:
            f.write(f"{encrypted_message}|srt|{key}")
        f.close()
        return
    def RestriveInfo(self):
        """Will Use To Store File Info In Edit Mood FTP"""
        with open(".info") as f:
            data=f.readline()
        key=data.split("|srt|")[1].replace("b'","").replace("'","")
        data=data.split("|srt|")[0].replace("b'","").replace("'","")
        decrypted_message = Fernet(key).decrypt(data)
        return decrypted_message.decode().split(">>")
    def Close_Connections(self):
        """Close ALl Connections From Remote Server"""
        if self.SSH:
              self.client.close()
        if self.FTP:
            self.ftp.close()
    def CheckFileServer(self,location,filename):
        """Checking File Existance In Remote Server"""
        (stdin, stdout, stderr) = self.client.exec_command(f"find {location} -name {filename} ")
        cmd_output = str(stdout.read())
        if filename in cmd_output : 
            return True
        else:
            return False
    def CheckFileLocal(self,location,filename):
        """Checking File Existance In Local System"""
        if not os.path.exists(f"{location}/{filename}"):
            print(f"File Dose Not Exists  {location}/{filename}")
            return False
        return True
    
    def DownloadFileServer(self,file,localAddress):
        """DownLoad File From Remote Server"""
        self.Connect_FTP()
        if not self.CheckFileServer(location=self.currnet_location,filename=file):
            print(f"It's Seems That File Does'n exists {file}")
            return False
        self.ftp.get(f"{self.currnet_location}/{file}",f"{localAddress}/{file}")
        return True
    def UploadFileServer(self,server_path,local_path,file_name):
        """
        The Function Works in Following steps
        1) Check That The Local File is Exists or not
        2) Check That Remote Server Have Same File  or not In The Givien Exmaple
        3) replace,Rename the according to User Command or Cancel The Porcess  
        """ 
        self.Connect_FTP()
        if not self.CheckFileLocal(local_path,file_name):
            return f"{local_path}/{file_name} File Does't Exists"
        if  self.CheckFileServer(server_path,file_name):
            procide=input(f"{file_name} Already Exists At {server_path} do you wanna Procide (y/n) default n ")
            if procide.lower()=="n":
                return f"{file_name} Alreay Exists"
        self.ftp.put(f"{local_path}/{file_name}",f"{server_path}/{file_name}")
    def UpdateFileServer(self,server_path,local_path,file_name):
        """
        The Function Works in Following steps
        1) Check That The Local File is Exists or not
        2) Check That Remote Server Have Same File  or not In The Givien Exmaple
        3) replace The Old FIle with Newone
        """ 
        self.Connect_FTP()
        if not self.CheckFileLocal(local_path,file_name):
            return f"{local_path}/{file_name} File Does't Exists"
        self.ftp.put(f"{local_path}/{file_name}",f"{server_path}/{file_name}")
    def ExeccuteCommand(self,command):
        """Execute Commands In Remote Server"""
        if not self.currnet_location:
           (stdin, stdout, stderr)= self.client.exec_command("pwd")
           self.currnet_location=stdout.read().decode().strip()
        if command.startswith("cd"):
           (stdin, stdout, stderr)= self.client.exec_command(f"cd {self.currnet_location} && {command} ; pwd")
           self.currnet_location=stdout.read().decode().strip()
        if True:
            (stdin, stdout, stderr) = self.client.exec_command(f"cd {self.currnet_location}; {command}")
            cmd_output = stdout.read().decode().strip()
            error=stderr.read().decode()
            if error:
                print(error)
                return ()
            return cmd_output 
        # return ""
              
def GetHostInfo(host):
    data=db.search(DB_search.host==host)
    if data:
        # data=data[0]
        message=Fernet(data[0]["rank"]).decrypt(data[0]["support"].replace("b'","").replace("'",""))
        message=message.decode().split(">>")
        return {"username":message[0],"port":message[1]}
    return {"username":"","port":22}

class Shell(cmd.Cmd):
    def __init__(self, completekey='tab', stdin=None, stdout=None,my_class=None) -> None:
        super().__init__(completekey, stdin, stdout)
        self.obj=my_class
    prompt = '>>> '
    def do_ls(self,inp):
        print(self.obj.ExeccuteCommand("ls"))
    def do_cd(self,inp):
        print(self.obj.ExeccuteCommand(f"cd {inp}"))
    
    # FTP Commands
    # File Gettings
    def do_getfile(self,inp):
        # print(f"Getting The File (Default: {os.getcwd()} ) ")
        local=os.getcwd()
        Connection.DownloadFileServer(file=inp,localAddress=local)
    def do_fedit(self,inp):
        local=os.getcwd()
        location=self.obj.currnet_location
        print(f"Gettting the Remote File '{location}/{inp}' To Local '{local}/'")
        self.obj.DownloadFileServer(location,inp,local)
        self.obj.StoreEditInfo(location,inp)
    def do_fupdate(self):
        try:
            ip,location,server_location,file=Connection.RestriveInfo()
        except:
            print("No Edit Has Found In This Folder")
        if  ip!=hostname:
            print("HOST Name MissMatched")
        Connection.UpdateFileServer(server_location,location,file)
        print(f"{file} Successfully Updated In {server_location}")
    
    def do_help(self, arg: str):
        return super().do_help(arg)
    def do_exit(self, inp):
        'Exit the application.'
        print('Closeing The Connections')
        Connection.Close_Connections()
        return super()


suggestion=WordCompleter([i["host"] for i in db.all()])
key = Fernet.generate_key()
hostname=prompt("Enter The Host Name (Remote IPv4) ",completer=suggestion)
data=GetHostInfo(hostname)
username=input("Enter The User Name (Remote Server) {} --> ".format(data["username"]))
port=input("Enter The Port Name (default={}) ".format(data["port"]))
password=input("Enter The Password (Kepp it Empty In Case of Password less connection) ")
port=port or 22
password=password or None
Connection=BaseClase(hostname,username or data["username"],port or data["port"] ,password)
Connection.Connect_SSH()
# Connection Done
# adding to Db
if not db.search(DB_search.host==hostname):
        message=f"{username}>>{port}".encode()
        db.insert({"rank":f"{key}".replace("b'","").replace("'",""),"host":hostname,"support":f"{Fernet(key).encrypt(message)}"})
# all done
shell = Shell(my_class=Connection)
shell.cmdloop()