
cat <<EOF
Go to Settings > Network.
Choose Adapter 1 > Attached to: Bridged Adapter.
Look for the IPv4 address under the eth0 or wlan0 section (it will look something like 192.168.x.x
EOF
sudo apt update
sudo apt install apache2
sudo systemctl status apache2
sudo systemctl start apache2
sudo ufw disable

sudo mkdir /var/www/html/mydirectory
# Step 1: Prompt user for input
echo "Enter the directory name to store:"
read directory_name

# Step 2: Create the directory using the user input
sudo mkdir /var/www/html/$directory_name
# Step 1: Get input from the user for source and destination paths
echo "Enter the path to your source files (e.g., /home/user/files):"
read source_path



# Step 2: Use the input paths in the cp command
sudo cp $source_path /var/www/html/$directory_name/ 

echo "Files have been copied from $source_path to $destination_path."
ip a
sudo ufw allow 80/tcp

echo "for firewall block "


