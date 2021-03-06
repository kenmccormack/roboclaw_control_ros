#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist
import roboclaw_driver.roboclaw_driver as rc
from std_msgs.msg import String

MTR_ADDRESS = 128 
MAX_DUTY_CYCLE = .15 
MIX_ROTATION = .5
def timer_callback(event):
    global last_time
    if(rospy.get_rostime() - last_time ).to_sec() > 1:
       rc.DutyM1M2(MTR_ADDRESS, 0, 0)
       rospy.loginfo("timeout on control")
    
    

def limit(value, limit):
    if value > limit:
	value = limit
    if value < -1 * limit:
	value = -1* limit
    return value


def twist_callback(msg):

    global pub
    global last_time 
    last_time = rospy.get_rostime()

    #rospy.loginfo("Linear Components: [%f, %f, %f]"%(msg.linear.x, msg.linear.y, msg.linear.z))
    #rospy.loginfo("Angular Components: [%f, %f, %f]"%(msg.angular.x, msg.angular.y, msg.angular.z))

    TR = MIX_ROTATION 
    v_l = msg.linear.x - TR * msg.angular.z
    v_r = msg.linear.x + TR * msg.angular.z

    dutyleft = int( v_l * MAX_DUTY_CYCLE * 32768)
    dutyright= int( v_r * MAX_DUTY_CYCLE * 32768)
    dutyleft = limit(dutyleft, 32767)
    dutyright = limit(dutyright, 32767)
    rc.DutyM1M2(MTR_ADDRESS, dutyleft, dutyright)

    rospy.loginfo("[%d , %d]"%(dutyleft, dutyright))
    dummy,c1,c2 = rc.ReadCurrents(MTR_ADDRESS)

    status = rc.ReadError(MTR_ADDRESS)[1]
    bvoltage =rc.ReadMainBatteryVoltage(MTR_ADDRESS)[1] / 10.0
    diagstr = "BattVoltage %f, Current[%f,%f], Status 0x%x" % (bvoltage, c1/100.0, c2/100.0, status)

    pub.publish(diagstr)
        



def move_robot():
    global pub 
    global last_time
    
    rc.Open('/dev/ttyUSB0',115200)
    print rc.ReadMinMaxMainVoltages(MTR_ADDRESS)

    pub = rospy.Publisher('motor_diagnostics', String, queue_size=10)
  

    rospy.init_node('roboclaw_ifc')

    last_time = rospy.get_rostime()
    rospy.Timer(rospy.Duration(1), timer_callback)
   
    rospy.Subscriber("/cmd_vel", Twist, twist_callback, queue_size=1)
    rospy.spin()

    rc.DutyM1M2(MTR_ADDRESS, 0, 0)


if __name__ == '__main__':
    try:
        #Testing our function
        move_robot()
    except rospy.ROSInterruptException: pass
