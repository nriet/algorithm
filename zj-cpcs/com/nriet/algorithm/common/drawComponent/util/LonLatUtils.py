def get_lon_lat(layer,dims,lon,lon_indexes,lat,lat_indexes):
    start_lon, end_lon, start_lat, end_lat = layer['draw_regions'].split(",")
    is_number_list = [is_number(value) for value in layer['draw_regions'].split(",")]
    dim_list = [dims[1], dims[1],dims[0],dims[0]]
    if (dim_list[0] != 'time'):
        if is_number_list[0]:
            start_lon = float(start_lon)
        else:
            start_lon = lon_indexes[0]
    else:
        if is_number_list[0]:
            start_lon = list(lon).index(float(start_lon))
        else:
            start_lon = lon_indexes[0]

    if (dim_list[1] != 'time'):
        if is_number_list[1]:
            end_lon = float(end_lon)
        else:
            end_lon = lon_indexes[-1]
    else:
        if is_number_list[1]:
            end_lon = list(lon).index(float(end_lon))
        else:
            end_lon = lon_indexes[-1]

    if (dim_list[2] != 'time'):
        if is_number_list[2]:
            start_lat = float(start_lat)
        else:
            start_lat = lat_indexes[0]
    else:
        if is_number_list[2]:
            start_lat = list(lat).index(float(start_lat))
        else:
            start_lat = lat_indexes[0]

    if (dim_list[3] != 'time'):
        if is_number_list[3]:
            end_lat = float(end_lat)
        else:
            end_lat = lat_indexes[-1]
    else:
        if is_number_list[3]:
            end_lat = list(lat).index(float(end_lat))
        else:
            end_lat = lat_indexes[-1]
    return end_lat, end_lon, start_lat, start_lon

def is_number(num):

    try:
        float(num)
        return True
    except:
        return False