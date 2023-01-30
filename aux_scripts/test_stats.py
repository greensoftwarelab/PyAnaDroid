import os
from pylab import *
import json, math
from os import listdir
import sys
from pylab import average

def get_avg(l):
    ret_val = None
    try:
        ret_val = average(l)
    except:
        pass
    return ret_val


def from_file(filepath):
    js = {}
    with open(filepath, 'r') as jj:
         js = json.load(jj)
    return js


def aggregate_test_stats(lookup_dir): # /Users/ruirua/repos/pyAnaDroid/anadroid_results/SampleApp--com.example.sampleapp/1.0.0/DroidbotAnnotation_17_05_22_13_11_14
    manafa_resume_files = [ os.path.join(lookup_dir, f) for f in listdir(lookup_dir) if 'manafa_resume' in f]
    manafa_resume_objs = [from_file(f) for f in manafa_resume_files]
    print(f"how many files? {len(manafa_resume_objs)}")
    total_energys = list(map(lambda x: x['global']['total_energy:'], manafa_resume_objs))
    print(total_energys)
    cpu_energys = list(map(lambda x: x['global']['per_component_consumption']['cpu'], manafa_resume_objs))
    elapseds = list(map(lambda x: x['global']['elapsed_time'], manafa_resume_objs))
    print(elapseds)
    print("cpus")
    print(cpu_energys)
    print(f"avg total consumption: {get_avg(total_energys)}")
    print(f"avg cpu consumption: {get_avg(cpu_energys)}")
    print(f"avg duration: {get_avg(elapseds)}")
    for cp in manafa_resume_objs[0]['global']['per_component_consumption'].keys():
        print(f"avg {cp} consumption: {get_avg(list(map(lambda x: x['global']['per_component_consumption'][cp], manafa_resume_objs)))}")


def boxplot_hd():
    vals = [
       [8.157804217191483, 20.688010331348835, 26.94716125001338, 20.6888090463285, 18.186040896462398, 22.565401765395826, 22.612969614367355, 18.180966039855537, 20.700123580219508, 18.156656569134864, 20.650533936540253, 26.97691079722396, 18.17658452078002, 31.49637478327852, 26.986544400079364, 18.14820387653495, 20.716612699457148, 26.93018153475847, 20.699037087098418, 22.565488007453883, 18.150811474848705, 51.146465697967336, 18.150075188528344, 51.32573950027934, 27.00180581136172],
        [21.423880278859016, 42.251806998527044, 18.90356046383547, 29.651975127443503, 17.629894772300936,
         50.94912458533618, 44.39747449547405, 28.180322633638, 20.602452607034483, 26.172094723550597,
         37.91624861987786, 20.618314017363765, 18.13931536171517, 18.92581352546258, 17.659784828997598,
         26.19830724219124, 38.09948863425523, 26.889745047755508, 28.565456107495166, 35.61430421063082,
         20.075096801936276, 53.69269680953549, 18.12980852538895, 23.33738054963436, 27.780891854035467],
        [27.018102465830243, 26.986122756721368, 18.13485505346239, 20.700405766168718, 36.63826098508669,
         26.97000332362047, 20.697554740604676, 22.550893606023514, 26.96576635818815, 18.166572395375095,
         26.95287436015892, 18.166934203339153, 31.491634952523835, 26.99569784755528, 18.192643591658996,
         26.992967852391242, 20.692084530428655, 20.70678128361099, 42.269940383211576, 31.482963808309954,
         20.720049827744845, 36.61852582988129, 18.14555120319931, 51.15536085217762, 18.158630780489908],
        [31.45336354636664, 31.22215779554325, 36.571605750107814, 18.930494843503418, 22.72189653231446,
         56.09133417112272, 21.418378694403188, 18.192939219297365, 38.063119692671826, 53.68483303460944,
         20.69208625211983, 21.530932003520263, 23.254667931390003, 20.81398364277536, 37.45593107866757,
         42.48353109542186, 26.46083472975104, 37.69068651513983, 37.87949398744909, 22.69450175833304,
         38.05676654042072, 23.605990010864733, 31.679515253278478, 18.128298117900968, 21.371745960523093]
    ]
    time_vals = [

        [74.4255039691925, 74.40104603767395, 74.36138606071472, 74.42097187042236, 74.54124093055725, 74.36015892028809, 74.51691007614136, 74.50336384773254, 74.46167206764221, 74.42079997062683, 74.28329014778137, 74.46054315567017, 74.50248098373413, 74.43390202522278, 74.47006487846375, 74.38615393638611, 74.52098608016968, 74.33156299591064, 74.44070196151733, 74.36044311523438, 74.39684200286865, 74.41916584968567, 74.39382410049438, 74.68001294136047, 74.51217913627625],
        [77.10048413276672, 74.33745884895325, 77.51775598526001, 74.21308493614197, 72.29484009742737,
         74.18302702903748, 78.13043904304504, 77.8178219795227, 74.1273238658905, 72.27225303649902, 77.06053304672241,
         74.20140385627747, 74.38381910324097, 77.60900902748108, 72.41741013526917, 72.34463691711426,
         77.43294787406921, 74.25398993492126, 78.88133883476257, 72.39868998527527, 72.24646806716919,
         78.15980505943298, 74.3618860244751, 76.93934297561646, 76.71482419967651],
        [74.64267110824585, 74.55432105064392, 74.38258504867554, 74.5139229297638, 74.48024487495422, 74.50978803634644, 74.52075219154358, 74.38054203987122, 74.4809958934784, 74.52977204322815, 74.46246600151062, 74.51416206359863, 74.49099397659302, 74.5807740688324, 74.63673114776611, 74.5732319355011, 74.50105690956116, 74.55397200584412, 74.40347695350647, 74.47048306465149, 74.60174489021301, 74.4401261806488, 74.46061301231384, 74.50039482116699, 74.49719095230103],
        [74.400465965271, 73.8535668849945, 74.36179995536804, 77.66382312774658, 74.96176505088806, 77.82123804092407,
         77.116051197052, 74.637943983078, 77.39452600479126, 74.49954414367676, 74.50106310844421, 77.5212950706482,
         76.70182991027832, 74.93994998931885, 76.15991687774658, 74.79659414291382, 74.46066117286682,
         76.63724994659424, 77.02115607261658, 74.8713870048523, 77.38160800933838, 77.86061000823975,
         74.95260500907898, 74.37274885177612, 76.94815182685852]
    ]
    vals = list(map(lambda x: sorted(x)[1:-1], vals))
    time_vals = list(map(lambda x: sorted(x)[1:-1], time_vals))
    keys = ['Monkey', 'Droibot', 'Monkey+I', 'Droidbot+I']
    print(get_avg(vals))
    print(get_avg(time_vals))
    gen_box_plot(keys, vals, 'Energy')
    gen_box_plot(keys, time_vals, 'time')
    #gen_violin_plot(keys, vals, 'Energy')


def gen_violin_plot(key_list, list_of_lists, title="ai"):
    # eg gen_box_plot(['group1', 'group2'], [[1, 2],[3, 4]]):
    fig1, en_box = plt.subplots()
    the_list = list_of_lists

    bp_dict = en_box.violinplot(the_list)
        # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['bodies']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])

    xtickNames = plt.setp(en_box, xticklabels=key_list)
    plt.setp(xtickNames, rotation=90, fontsize=10)
    plt.suptitle(title)
    plt.show()


def gen_box_plot(key_list, list_of_lists, title="ai"):
    # eg gen_box_plot(['group1', 'group2'], [[1, 2],[3, 4]]):
    fig1, en_box = plt.subplots()
    the_list = list_of_lists

    bp_dict = en_box.boxplot(x=the_list,
                             notch=False,  # notch shape
                             vert=True,  # vertical box aligmnent
                             sym='ko',  # red circle for outliers
                             patch_artist=True,  # fill with color
                             )
    i = 0
    for line in bp_dict['medians']:
        x, y = line.get_xydata()[1]  # top of median line
        xx, yy = line.get_xydata()[0]
        text(x, y, '%.2f' % y, fontsize=8)  # draw above, centered
        # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
        i = i + 1

        # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['boxes']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])

    xtickNames = plt.setp(en_box, xticklabels=key_list)
    plt.setp(xtickNames, rotation=45, fontsize=8)
    plt.suptitle(title)
    plt.show()


if __name__ == '__main__':
    boxplot_hd()
    if len(sys.argv) > 1:
        aggregate_test_stats(sys.argv[1])
    else:
        print("error. provide input dir")