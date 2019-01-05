from netmiko import ConnectHandler


class BaseConnection():
    def __init__(self, device_type, device_ip, port, username="", password=""):
        self._device_type = device_type
        self._device_ip = device_ip
        self._port = port
        self._username = username
        self._password = password
        self._conn = None   #placeholder for connection cache

    def connect(self):
        try:
            if(self._conn == None):
                self._conn = ConnectHandler(device_type=self._device_type, ip=self._device_ip, port=self._port, username=self._username, password=self._password)
            return self._conn
        except Exception as e:
            print(str(e))
            return None

    def check_connection(self):
        return self.connect() is not None

    def send_command(self, cmd):
        conn = self.connect()
        if conn is None:
            return ""
        return self._conn.send_command(cmd)

    def ping_status(self, target_ip, detailed=False):
        """
        Pings an IP from this device

        :param target_ip: Target IP to ping from this device
        :param detailed: if True, then returns complete ping command output
        :return: if Success rate is greater than 0 then return True else return False
        """
        op = self.send_command("ping {}".format(target_ip))
        if detailed:    # send the returned string of ping command
            return op
        if str(op).find("Success rate is ") > -1:
            if int(str(op).splitlines()[3].split()[3]) == 0:   # if Success rate is 0 then return False else return True
                return False
            else:
                return True
        else:
            return False


class RouterConnection(BaseConnection):
    def __init__(self, device_type, device_ip, port, username, password):
        super().__init__(device_type, device_ip, port, username, password)
        self.bgp = RouterBGP(self)
        self.connect()

    def reset_prompt(self):
        if self._conn.check_config_mode():
            self._conn.exit_config_mode()
        if self._conn.check_enable_mode():
            self._conn.exit_enable_mode()

    def get_interfaces(self, only_drop=False):
        op = self.send_command("show interfaces")
        if not op or op == "":
            return ""
        if only_drop:
            lines = op.splitlines()
            s = ""
            # print(op)
            for i in range(0, len(lines)):
                if not lines[i].startswith("  "):   # this is the first line of block
                    current_block_start_line_no = i
                else:   # this is one of details for the current interface block
                    if lines[i].find("Total output drops:") > -1:
                        if lines[i].split()[lines[i].split().__len__() - 1] != "0":     # show this block
                            for x in range(current_block_start_line_no, len(lines)):
                                s += lines[x] + "\n"
                                if x != current_block_start_line_no and not lines[x].startswith("  "):  # store in return variable until next interface block starts
                                    break
            return s

            # intf_count = 0
            # for i in range(0, len(lines), 26):
            #     print(i)
            #     print(lines[10 + i].split())
            #     if lines[10 + intf_count*26].split()[7] != "0":
            #         for j in range(26):
            #             s += lines[j + intf_count * 26] + "\n"
            #     intf_count += 1
            return s
        return op

    def get_interfaces_ip(self, detailed=False, only_with_ip=False):
        if detailed:
            op = self.send_command("show ip int")
        else:
            op = self.send_command("show ip int br")
            if only_with_ip:
                lines = op.splitlines()
                s = ""
                for i in range(1, len(lines)):
                    if lines[i].find("unassigned") == -1:
                        s += lines[i] + "\n"
                op = s
        if not op or op == "":
            return ""
        return op

    def get_cpu_utilization_processes(self, detailed=False, top=1, only_proc_name=False):
        op = self.send_command("show process cpu sorted")
        if detailed:
            return op
        lines = op.splitlines()
        s = ""
        for i in range(2, 2+top):
            if i > len(lines):
                return s
            if only_proc_name:
                s += lines[i].split()[8] + "\n"
            else:
                s += str(lines[i] + "\n")
        return s

    def get_cpu_utilization(self, five_sec=True, one_min=False, five_min=False):
        # "CPU utilization for five seconds: 0%/0%; one minute: 0%; five minutes: 0%"
        op = self.send_command("show process cpu sorted")
        if not op:
            return ""
        s = ""
        tokens = op.split()
        if five_sec:
            s += "five seconds: {}".format(tokens[5])
        if one_min:
            s += "one minute: {}".format(tokens[8])
        if five_min:
            s += "five minutes: {}".format(tokens[11])
        return s

    def get_log(self):
        self._conn.enable()
        # self._conn.config_mode()
        self.send_command("show logging")
        self.reset_prompt()


class RouterBGP():
    def __init__(self, base_connection):
        self._base_connection = base_connection

    def get_bgp_summary(self, detailed=True):
        op = self._base_connection.send_command("show IP bgp summary")
        if detailed:
            return op

    def is_neighbour_down(self):
        """
        Checks if any neighbor is down

        :return:    False: if no neighor is down
                    list : list of Idle neighbors in format [ [neighbor ip, bgp neighbor summary for this neighbor] ]
        """
        summary = self.get_bgp_summary()
        down_nbr = []
        if summary and len(summary.split("\n")) > 4 :
            rows = summary.split("\n")
            for i in range(4, len(rows)):
                is_idle = str(rows[i]).split()[9] == 'Idle'
                if is_idle:
                    down_nbr.append([str(rows[i]).split()[0], str(rows[i])])
            if len(down_nbr) > 0:
                return down_nbr
            return False

    def get_next_hop_interface(self, target_ip):
        op = self._base_connection.send_command("show ip cef " + target_ip)
        if not op or op == "":
            return None
        return op.splitlines()[1].split()[2]


class CommonFunctions:
    @staticmethod
    def fatal(msg, exit_code=1):
        import sys
        print("{} . Exiting..".format(str(msg)))
        sys.exit(exit_code)

#
# class RouterTroubleshooting:
#     @staticmethod
#     def get_bgp_down_rca(router_connection, neighbor_ip):
#         """
#         :param router_connection: instance of RouterConnection
#         :param neighbor_ip: IP of neighbor which BGP flapped
#         :return: prints the individual status check
#         """
#         if not isinstance(router_connection, RouterConnection):
#             CommonFunctions.fatal("Please supply valid RouteConnection object for router_connection")
#         print("Checking if any BGP neighbor is down: ", end='')
#         lst = router_connection.bgp.is_neighbour_down()
#         if not lst:
#             print("Pass. No neighbour is down")
#         else:
#             print("Fail. Following neighbors are down:")
#             for nbr in lst:
#                 print(nbr)
#
#         print("Checking neighbor Ping status: ", end='', flush=True)
#         # router_connection.
#         print("Checking top CPU utilization: ", end='', flush=True)
#         return ""

# -------------------------------------------------------------------------------------------------------------

#
# if __name__ == "__main__":
#     from datetime import datetime
#     start = datetime.now()
#
#     router1 = RouterConnection("cisco_ios_telnet", "192.168.1.11", "2001", "root", "cisco")
#     # router2 = RouterConnection("cisco_ios_telnet", "192.168.1.11", "2002", "root", "cisco")
#
#     if not router1.check_connection():
#         CommonFunctions.fatal("Connection could not be made with some router1")
#     # if(router2.check_connection() == False):
#     #     CommonFunctions.fatal("Connection could not be made with some router2")
#
#     # print(router1.bgp.get_bgp_summary())
#     # print("\n---------------------------------")
#     # print(router1.bgp.is_neighbour_down())
#     # print("\n---------------------------------")
#     # print(router1.ping_status("2.2.2.2"))
#     # print("\n---------------------------------")
#     # print(router1.get_cpu_utilization())
#     # print("\n---------------------------------")
#     # print(router1.get_interfaces_ip(only_with_ip=True))
#     # print("\n---------------------------------")
#     # print(router1.get_interfaces(only_drop=False))
#
#     # RouterTroubleshooting.get_bgp_down_rca(router1, "2.2.2.2")
#
#     print("Time taken: ", format(datetime.now() - start))
#
