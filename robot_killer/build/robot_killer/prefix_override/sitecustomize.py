import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/zlove/botFire/Autobot/robot_killer/install/robot_killer'
