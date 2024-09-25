from pymodbus.client import ModbusSerialClient as ModbusClient
import time

# from pymodbus.utilities import computeCRC

# # Example usage
# message = [0x09, 0x10, 0x03, 0xE8, 0x00, 0x03, 0x06,
#            0x09, 0x00, 0x00, 0xFF, 0xFF, 0xFF]
# crc = computeCRC(message)
# print(f"CRC: {crc:04X}")
    
class Robotiq85():
    def __init__(self, MODBUS_PORT='/dev/ttyUSB0', BAUDRATE=115200) -> None:
        self.SPEED = 20
        self.FORCE = 20
        self.client = ModbusClient(
            port=MODBUS_PORT,
            baudrate=BAUDRATE,
            timeout=1,
            parity='N',
            stopbits=1,
            bytesize=8
        )

    
    def gripper_activate(self, slave=9):
        # Assuming 'activate' writes to registers starting at address 1000 (0x03E8)
        address = 0x03E8
        values = [0x0000, 0x0000, 0x0000]  # Activation values
        response = self.client.write_registers(address, values, slave=slave)

        # if response.isError():
        #     print("Activation failed.")
        #     return False
        # else:
        #     print("Activation command sent.")

        # Read the gripper status until it's activated

        status_address = 0x07D0  # Address to read gripper status
        while True:
            response = self.client.read_holding_registers(status_address, 1, slave=slave)
            if response.isError():
                print("Error reading gripper status.")
                return False

            status = response.registers[0]
            # Check activation bit/status (modify the condition based on actual device response)
            if status == 0x0000:
                # print("Gripper activated.")
                break
            else:
                print("Waiting for activation...")
                time.sleep(0.5)  # Wait before polling again
        
        # self.open()
        return True


    def close(self, slave=9):
        if not self.client.connect():
            print("Failed to connect to the Modbus server.")
            return

        if not self.gripper_activate():
            print("Failed to activate gripper.")
            self.client.close()
            return
        
        # Command to close the gripper
        address = 0x03E8
        # Construct the command value based on speed and force
        # Assuming register values: [command, position, speed_force]
        command = 0x0900  # Close command with necessary bits set
        position = 0x00FF  # Closed position
        speed_force = (self.SPEED << 8) | self.FORCE  # Combine speed and force into one register
        values = [command, position, speed_force]

        response = self.client.write_registers(address, values, slave=slave)
        time.sleep(2)
        # if response.isError():
        #     print("Failed to send close command.")
        #     return False
        # else:
        #     print("Gripper close command sent.")

        # Monitor until the gripper has completed the operation
        # return monitor_gripper_status(self.client, target_status='closed', slave=slave)

    def open(self, slave=9):
        if not self.client.connect():
            print("Failed to connect to the Modbus server.")
            return

        if not self.gripper_activate():
            print("Failed to activate gripper.")
            self.client.close()
            return
        
        # Command to open the gripper
        address = 0x03E8
        # Construct the command value based on speed and force
        command = 0x0900  # Open command with necessary bits set
        position = 0x0000  # Open position
        speed_force = (self.SPEED << 8) | self.FORCE  # Combine speed and force into one register
        values = [command, position, speed_force]

        response = self.client.write_registers(address, values, slave=slave)
        time.sleep(0.8)
        # if response.isError():
        #     print("Failed to send open command.")
        #     return False
        # else:
        #     print("Gripper open command sent.")

        # Monitor until the gripper has completed the operation
        # return monitor_gripper_status(self.client, target_status='open', slave=slave)


    def monitor_gripper_status(self, target_status, slave=9):
        import time

        status_address = 0x07D0  # Address to read gripper status
        while True:
            response = self.client.read_holding_registers(status_address, 1, slave=slave)
            if response.isError():
                print("Error reading gripper status.")
                return False

            status = response.registers[0]
            # Decode the status register to determine if the operation is complete
            # This requires understanding the specific bits used by your gripper
            if target_status == 'closed':
                # Replace with actual condition based on your device's status bits
                if (status & 0x0001):  # Hypothetical bit indicating closed
                    print("Gripper has closed.")
                    break
            elif target_status == 'open':
                if (status & 0x0002):  # Hypothetical bit indicating open
                    print("Gripper has opened.")
                    break
            else:
                print("Unknown target status.")
                return False
            time.sleep(0.5)  # Wait before polling again
        return True



if __name__ == '__main__':
    gripper = Robotiq85
    gripper.close()
    gripper.open()