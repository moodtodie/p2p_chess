import hashlib


def calculate_checksum(content):
    """
    Calculate the checksum for a page using SHA-256.
    """
    # Create a new SHA-256 hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the bytes of the content
    hash_object.update(content.encode('utf-8'))

    # Get the hexadecimal representation of the hash digest
    checksum = hash_object.hexdigest()

    return checksum


def check_checksum(packet):
    packet_parts = packet.split('\r\n')
    getting_checksum = packet_parts[1]
    checksum = calculate_checksum(packet_parts[0])
    if getting_checksum == checksum:
        return True
    return False


def handle_packet(packet):
    if check_checksum(packet):
        t_packet = (packet.split('\r\n')[0]).split('\n')
        dst_key = t_packet[0]
        src_key = t_packet[1]
        is_service = t_packet[2] == 'True'
        data = t_packet[3]
        if not is_service:
            data = data.split('\t')
        return dst_key, src_key, is_service, data
    else:
        return None


def create_data(player, pos1, pos2, num_of_turn):
    return f'{player}\t{pos1}\t{pos2}\t{num_of_turn}'


def create_packet(dst_key, src_key, is_service, data):
    packet = f'{dst_key}\n{src_key}\n{is_service}\n{data}'
    checksum = calculate_checksum(packet)
    return f'{packet}\r\n{checksum}'
