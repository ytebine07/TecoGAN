import os, sys, datetime
import cv2 as cv
import argparse
import youtube_dl

from lib.data import video


# ------------------------------------parameters------------------------------#
parser = argparse.ArgumentParser(description='Process parameters.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--start_id', default=2000, type=int, help='starting scene index')
parser.add_argument('--duration', default=120, type=int, help='scene duration')
parser.add_argument('--disk_path', default="/mnt/netdisk/data/video/", help='the path to save the dataset')
parser.add_argument('--summary_dir', default="", help='the path to save the log')
parser.add_argument('--REMOVE', action='store_true', help='whether to remove the original video file after data preparation')
parser.add_argument('--TEST', action='store_true', help='verify video links, save information in log, no real video downloading!')

Flags = parser.parse_args()

if Flags.summary_dir == "":
    Flags.summary_dir = os.path.join(Flags.disk_path, "log/")
os.path.isdir(Flags.disk_path) or os.makedirs(Flags.disk_path)
os.path.isdir(Flags.summary_dir) or os.makedirs(Flags.summary_dir)

link_path = "https://www.youtube.com/watch?v="
video_data_dict = {
# Videos and frames are hard-coded.
# We select frames to make sure that there is no scene switching in the data
# We assume that the Flags.duration is 12
    "nakI7otES74" : [0, 310,460,720,860], #1
}

# ------------------------------------log------------------------------#
def print_configuration_op(FLAGS):
    print('[Configurations]:')
    for name, value in FLAGS.__dict__.items():
        print('\t%s: %s'%(name, str(value)))
    print('End of configuration')
    
class MyLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        now_str = datetime.datetime.now().strftime("%m%d%H%M")
        self.log = open(Flags.summary_dir + "logfile_%s.txt"%now_str, "a") 

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message) 

    def flush(self):
        self.log.flush()
        
sys.stdout = MyLogger()
print_configuration_op(Flags)


# ------------------------------------tool------------------------------#
def gen_frames(infile, outdir, width, height, start, duration, savePNG=True):
    print("folder %s: %dx[%d,%d]//2 at frame %d of %s"
        %(outdir, duration, width, height, start,infile,))
    
    if savePNG:
        cam = video.create_capture(infile)
        for i in range(duration):
            colFull = video.getImg(cam, i+start) 
            filename = outdir+'col_high'+("_%04d.png"%(i))
            cv.imwrite( filename, colFull)


# ------------------------------------main------------------------------#
cur_id, valid_video, try_num = Flags.start_id, 0, 0

for keys in video_data_dict:
    try_num += len(video_data_dict[keys])
print("Try loading %dx%d."%(try_num, Flags.duration))
             
ydl = youtube_dl.YoutubeDL( 
    {'format': 'bestvideo/best',
     'outtmpl': os.path.join(Flags.disk_path, '%(id)s.%(ext)s'),})
     
saveframes = not Flags.TEST
for keys in video_data_dict:
    tar_vid_input = link_path + keys
    print(tar_vid_input)
    info_dict = {"width":-1, "height": -1, "ext": "xxx", }
    
    # download video from vimeo
    try:
        info_dict = ydl.extract_info(tar_vid_input, download=saveframes)
        # we only need info_dict["ext"], info_dict["width"], info_dict["height"]
    except KeyboardInterrupt:
        print("KeyboardInterrupt!")
        exit()
    except:
        print("youtube_dl error:" + tar_vid_input)
        pass
    
    # check the downloaded video
    tar_vid_output = os.path.join(Flags.disk_path, keys+'.'+info_dict["ext"])
    if saveframes and (not os.path.exists(tar_vid_output)):
        print("Skipped invalid link or other error:" + tar_vid_input)
        continue
    if info_dict["width"] < 400 or info_dict["height"] < 400:
        print("Skipped videos of small size %dx%d"%(info_dict["width"] , info_dict["height"] ))
        continue
    valid_video = valid_video + 1
    
    # get training frames
    for start_fr in video_data_dict[keys]:
        tar_dir = os.path.join(Flags.disk_path, "scene_%04d/"% cur_id)
        if(saveframes):
            os.path.isdir(tar_dir) or os.makedirs(tar_dir)
        gen_frames(tar_vid_output, tar_dir, info_dict["width"], info_dict["height"], start_fr, Flags.duration, saveframes)
        cur_id = cur_id+1
        
    if saveframes and Flags.REMOVE:
        print("remove ", tar_vid_output)
        os.remove(tar_vid_output)
        
print("Done: get %d valid folders with %d frames from %d videos." % (cur_id - Flags.start_id, Flags.duration, valid_video))

