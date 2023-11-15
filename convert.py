import argparse
import rosbag
import pandas as pd
from datetime import datetime


def map_fn(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


# Function to convert ROS Time to datetime object
def ros_time_to_datetime(ros_time):
    return datetime.fromtimestamp(ros_time.to_sec())


def main(rosbag_path, adc_fields, vcc=3.3, adc_vcc=3.3):
    adc_resolution = 65536  # 16-bit ADC
    voltage_data = {
        field: [] for field in adc_fields
    }  # Dictionary to store data for each field
    timestamps = []

    # Open the rosbag file
    with rosbag.Bag(rosbag_path, "r") as bag:
        # Iterate over each message in the specified topic
        for _, msg, t in bag.read_messages(topics=["/state"]):
            # Extract and convert the data from each field
            for field in adc_fields:
                adc_value = getattr(
                    msg, field
                )  # Dynamically get the ADC value from the field

                """
                syntax: sensor(input) -> output

                Flow of current data
                1. ACS_current_sensor(motor)-> (0,VDD), where VDD = 3.3v
                2. ADS1115(-VDD,VDD) -> (0,2^16), where VDD = 3.3v, this is the measured in rosbag
                """

                # ranges from -adc_vcc to adc_vcc: https://user-images.githubusercontent.com/41026849/283148624-09d723a2-41b0-4b52-8733-5fc47f7d5e53.png
                vout = map_fn(adc_value, 0, adc_resolution, -adc_vcc, adc_vcc)
                print(vout, " ", adc_value)
                if "exc" in field:
                    # adding this results in expected 0A to be 0A, not sure why
                    WEIRD_OFFSET = 80

                    # from ACS711EX Current Sensor Carrier -31A to +31A https://www.pololu.com/product/2453 -> electrical connections
                    i = 73.3 * (vout / vcc) - 36.7 + WEIRD_OFFSET
                else:
                    # from ACS711EX Current Sensor Carrier -15.5A to +15.5A https://www.pololu.com/product/2453 -> electrical connections

                    # adding this results in expected 0A to be 0A, not sure why
                    WEIRD_OFFSET = 40
                    i = 36.7 * (vout / vcc) - 18.3 + WEIRD_OFFSET
                voltage_data[field].append(i)
            # Record the timestamp
            timestamps.append(ros_time_to_datetime(t))

    # Create a DataFrame with the timestamps as the index
    voltage_df = pd.DataFrame(voltage_data, index=timestamps)
    voltage_df.index.name = "Time"

    # Save the DataFrame to a CSV file
    csv_path = rosbag_path.replace(".bag", "_current_data.csv")
    voltage_df.to_csv(csv_path)

    print(f"Data saved to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract ADC voltage data from a ROS bag file."
    )
    parser.add_argument("rosbag_path", type=str, help="The path to the ROS bag file.")
    parser.add_argument(
        "adc_fields",
        nargs="+",
        help="A list of field names within the /state topic message that contain the ADC values.",
    )
    args = parser.parse_args()

    main(args.rosbag_path, args.adc_fields)
