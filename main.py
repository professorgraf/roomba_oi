

from create2oi import roomba
import time

# demonstration of the roomba open interface 
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    r = roomba.Roomba(port="/dev/cu.usbserial-AC01OAX0")
    r.start(roomba.RoombaConstants.SAFE)

    # only reset in case some problems occur
    # r.reset()
    # print(r.info)
    # r.start(roomba.RoombaConstants.SAFE)

    # r.drive(50, 0x8000)
    # time.sleep(1)
    r.readbatterystate()
    print(r.battery.voltage)

    for i in range(1, 50):
        # r.readsensordata(1)
        #r.readenvironmentalsensors()
        #print("bump right is {}".format(r.sensors.bump_right))
        #print("bump left is {}".format(r.sensors.bump_left))

        r.readlightbumpers()
        for i in range(0, 6):
            if r.sensors.light_bumper_signal[i] > 300:
                print("light bump {} is {}".format(i, r.sensors.light_bumper_signal[i]))

    r.stop()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
