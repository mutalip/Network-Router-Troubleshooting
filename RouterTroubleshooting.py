from RouterHelper import *

class RouterTroubleshooting:
    def __init__(self, router_connection):
        """
        :param router_connection: instance of RouterConnection
        """
        self._router_connection = router_connection
        if not isinstance(router_connection, RouterConnection):
            CommonFunctions.fatal("Please supply valid RouteConnection object for router_connection")

    def get_bgp_down_rca(self, neighbor_ip):
        """
        :param neighbor_ip: IP of neighbor which BGP flapped
        :return: prints the individual status check
        """
        print("Checking if any BGP neighbor is down: \t", end=' ')
        lst = self._router_connection.bgp.is_neighbour_down()
        if not lst:
            print("Pass. No neighbour is down")
        else:
            print("Fail. Following neighbors are down:")
            for nbr in lst:
                print(nbr)

        print("Checking neighbor Ping status: \t", end='')
        if not self._router_connection.ping_status(target_ip=neighbor_ip):
            print("Fail. Neighbour ping failure")
        else:
            print("Pass. Neighbour pinging")

        print("Checking top CPU utilization: \t", end='')
        print("{}  --top--{}".format(self._router_connection.get_cpu_utilization(), self._router_connection.get_cpu_utilization_processes()))
        return ""

    def poll(self, seconds=-1, interval=1):
        import time
        print("Polling every {} seconds".format(interval))
        while True:
            print(".", end='', flush=True)
            time.sleep(interval)


# -------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    from datetime import datetime
    start = datetime.now()

    router1 = RouterConnection("cisco_ios_telnet", "192.168.1.11", "2001", "root", "cisco")
    # router2 = RouterConnection("cisco_ios_telnet", "192.168.1.11", "2002", "root", "cisco")

    if not router1.check_connection():
        CommonFunctions.fatal("Connection could not be made with some router1")
    # if(router2.check_connection() == False):
    #     CommonFunctions.fatal("Connection could not be made with some router2")

    # print(router1.bgp.get_bgp_summary())
    # print("\n---------------------------------")
    # print(router1.bgp.is_neighbour_down())
    # print("\n---------------------------------")
    # print(router1.ping_status("2.2.2.2"))
    # print("\n---------------------------------")
    # print(router1.get_cpu_utilization())
    # print("\n---------------------------------")
    # print(router1.get_interfaces_ip(only_with_ip=True))
    # print("\n---------------------------------")
    # print(router1.get_interfaces(only_drop=False))
    rca = RouterTroubleshooting(router1)
    # rca.get_bgp_down_rca("2.2.2.2")
    rca.poll()

    print("Time taken: ", format(datetime.now() - start))