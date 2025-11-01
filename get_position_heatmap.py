import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
from PIL import Image
import cv2
from libs.common.constants.league_constants import MAP_HEIGHT, MAP_WIDTH
import os, json

class LeaguePositionHeatmap:
    
    def __init__(self, grid_size: int = 100):
        self.__cell_width = MAP_WIDTH / grid_size
        self.__cell_height = MAP_HEIGHT / grid_size
        self.__grid_size = grid_size
    
    def create_position_heatmap(self, positional_frames: list[dict], player_idx: int):
        '''
        Creates a heatmap based on player's position.
        🔴 RED (HOT)     = Spent LOTS of time here (80-100% intensity)
        🟠 ORANGE        = Spent SIGNIFICANT time (60-80%)
        🟡 YELLOW        = Spent MODERATE time (40-60%)
        🟢 GREEN         = Spent SOME time (20-40%)
        🔵 BLUE (COOL)   = Spent LITTLE time (5-20%)
        ⚪ WHITE (COLD)  = NEVER visited (0-5%)
        
        Takes in positional_frames list that contains frame object per minute
        Takes in player_idx that indicates the player's order in the list of participants (0-th index)
        '''
        
        heatmap = np.zeros((len(positional_frames), 2))
        
        for i, frame in enumerate(positional_frames):
            try:
                participant_frames = frame.get('participantFrames', None)
                assert isinstance(participant_frames, dict)
                
                player_frame = participant_frames.get(str(player_idx + 1), None)
                assert isinstance(player_frame, dict)
                
                p_x, p_y = player_frame['position']['x'], player_frame['position']['y']
                if p_x > MAP_WIDTH or p_y > MAP_HEIGHT:
                    # out of bounds coordinates --> because of player death/temporary offset when TP
                    continue
                grid_x = int(p_x / self.__cell_width)
                grid_y = int(p_y / self.__cell_height)
                
                heatmap[i, 0] = grid_x
                heatmap[i, 1] = grid_y
                
            except AssertionError as ae:
                raise SystemError('create_position_heatmap - AssertionError:', ae)
        
        # Smooth to make it look nice (spread heat to nearby cells)
        # heatmap = gaussian_filter(heatmap, sigma=2.0)
            
        # # Normalize to 0-1 range
        # heatmap = heatmap / np.max(heatmap)
        
        return heatmap


if __name__ == '__main__':
    
    LPH = LeaguePositionHeatmap(100)
    
    minimap_image = Image.open(os.path.join(os.getcwd(), 'league_minimap.png'))
    minimap_size = minimap_image.size
    
    colors = ['black', 'darkred', 'red', 'orange', 'yellow', 'white']
    n_bins = 256
    

    for puuid_folder in os.listdir(os.path.join(os.getcwd(), 'rank_timelines', 'challenger_timelines')):
        for match_timeline_folder  in os.listdir(os.path.join(os.getcwd(), 'rank_timelines', 'challenger_timelines', puuid_folder)):
            if os.path.isfile(os.path.join(os.getcwd(), 'rank_timelines', 'challenger_timelines', puuid_folder, match_timeline_folder)):
                with open(os.path.join(os.getcwd(), 'rank_timelines', 'challenger_timelines', puuid_folder, match_timeline_folder), 'r', encoding='utf-8') as f:
                    match_timelines = json.load(f)
                    for match_timeline in match_timelines:
                        player_idx = match_timeline['metadata']['participants'].index(puuid_folder)
                        p_heatmap = LPH.create_position_heatmap(match_timeline['info']['frames'], player_idx)
                        
                        # # Resize heatmap to match minimap size
                        # p_heatmap_resized = cv2.resize(p_heatmap, minimap_size, interpolation=cv2.INTER_LINEAR)
                        
                        # # Create transparent heatmap
                        # cmap = LinearSegmentedColormap.from_list('custom_hot', colors, N=n_bins)
                        
                        # # Apply colormap to heatmap
                        # colored_heatmap = cmap(p_heatmap_resized)
                        
                        # # Adjust alpha channel based on heatmap intensity
                        # # Low intensity = more transparent
                        # # High intensity = more opaque
                        # colored_heatmap[..., 3] = p_heatmap_resized * 0.6
                        
                        # # Convert to PIL Image
                        # heatmap_img = Image.fromarray((colored_heatmap * 255).astype(np.uint8), 'RGBA')
                        
                        # # Paste transparent heatmap on top of minimap
                        # combined = minimap_image.copy().convert('RGBA')
                        # combined = Image.alpha_composite(combined, heatmap_img)
                        
                        # plt.imshow(combined, interpolation='bilinear')
                        plt.figure(figsize=(10, 10))
                        plt.scatter(p_heatmap[:, 0], p_heatmap[:, 1])
                        # plt.colorbar(label='Time Spent')
                        plt.title(f"Position Heatmap - match: {match_timeline['metadata']['matchId']}, puuid: {puuid_folder}")
                        plt.show()
                        
                        
        
        