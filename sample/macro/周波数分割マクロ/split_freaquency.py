from split import create_file, cyclic_split, file_open, from_num_to_10Exx


def split(path):
    f_num = int(input("frequency column number (start from 0) is ->"))
    data_list, filename, dirpath, label = file_open(path)
    data_list_list = cyclic_split(data_list, 16)
    for data_list_f in data_list_list:
        new_filepath = (
            f"{dirpath}/{filename}_{from_num_to_10Exx(data_list_f[0][f_num])}Hz.txt"
        )
        create_file(new_filepath, data_list_f, label)

    print("finish!")
