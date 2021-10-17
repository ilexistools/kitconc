# Designed and implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

import os 
from PIL import Image, ImageColor, ImageFont, ImageDraw
import math
import random
from kitconc import wordle_spirals as SP
from kitconc import wordle_bbox
from kitconc import wordle_trees
from kitconc import wordle_colorhandler as CH
import tempfile 


# vertical constant:
VERTICAL_DISABLED = 0

# stretch sizes constants:
STRETCH_SIZE_10 = 0.1
STRETCH_SIZE_25 = 0.25
STRETCH_SIZE_50 = 0.5
STRETCH_SIZE_75 = 0.75
STRETCH_SIZE_95 = 0.9
STRETCH_SIZE_100 = 1

# color themes constants:
THEME_RANDOM_COLORS = 0
THEME_JET_COLORS = 1
THEME_GRAYISH_COLORS = 2
THEME_FIXED_COLORS = 3
THEME_BRFLAG = 4

#from cython_wordle.main import interActive
interActive = False
# constants:
TOKENS_TO_USE = 400       # number of different tokens to use in the wordle
STAY_AWAY = 2             # force any two words to stay at least this number of pixels away from each other
FONT_SIZE_MIN = 10        # the smallest font of a word
FONT_SIZE_MAX = 300       # the largest font of a word, might go slightly above this value
DESIRED_HW_RATIO = 0.618  # height/widht ratio of the canvas
QUADTREE_MINSIZE = 5      # minimal height-width of the box in quadTree partition
FONT_NAME = os.path.dirname(os.path.abspath(__file__)) +  "/data/ubuntu.ttf"   # the font (true type) used to draw the word shapes



class Token:
    """
        encapsulates the main information on a token into a single class
        Token here represents a word to be placed on canvas for the final wordle Image

        most of the attributes are filled with functions during processing of the tokens
    """

    def __init__(self, word, fontSize = 10, drawAngle = 0):
        self.word = word
        self.fontSize = fontSize      # an integer
        self.drawAngle = drawAngle    # an integer representing the rotation angle of the image; 0 - for NO rotation
        self.imgSize = None           # integers (width, height) size of the image of this word with the given fontSize
        self.quadTree = None          # the quadTree of the image of this word with the above characteristics
        self.place = None             # tuple, the coordinate of the upper-left corner of the token on the final canvas
        self.color = None             # the fill color on canvas (R, G, B) triple


def proposeCanvasSize(normalTokens):
    """
      Given a list of normalized tokens we propose a canvase size (width, height)
      based on the areas covered by words. The areas are determined via leaves of the
      corresponding quadTrees.

      It is assumed that tokens come sorted (DESC), i.e. bigger sized words come first.
      We use this assumption when enforcing the canvas size to be larger
      than total area of the bounding boxes of the first few tokens.
    """

    area = 0         # the area covered by the quadTrees, i.e. the actual shape of the token
    boxArea = []     # the areas covered by the bounding box of the tokens

    for token in normalTokens:
        area += token.quadTree.areaCovered()
        boxArea.append( wordle_trees.rectArea(token.quadTree.root.value) )

    ensure_space = 5    # force the sum of the total area to cover at least the first @ensure_space tokens

    total = area + sum ( boxArea[:ensure_space] )
    w = int( math.sqrt(total/DESIRED_HW_RATIO) ) + 1
    h = int(DESIRED_HW_RATIO*w) + 1

    #print('Ratio of the area covered by trees over the total area of bounding boxes of words',  area/sum(boxArea))
    return w, h

def randomFlips(n, p):
    """
     Return an array of length n of random bits {0, 1} where Probability(0) = p and Probability(1) = 1 - p
     this is used for randomly selecting some of the tokens for vertical placement.
    """
    ans = n*[0]
    for i in range(n):
        x = random.random()
        if x > p:
            ans[i] = 1

    return ans


def normalizeWordSize(tokens, freq, N_of_tokens_to_use, horizontalProbability = 1.0):
    """
     (linearly) scale the font sizes of tokens to a new range depending on the ratio of the current min-max
     and take maximum @N_of_tokens_to_use of these tokens
     allow some words to have vertical orientation defined by @horizontalProbability
    """

    words = tokens[:N_of_tokens_to_use]
    sizes = freq[:N_of_tokens_to_use]

    normalTokens = [ ] # the list of Tokens to be returned

    # scale the range of sizes; the scaling rules applied below are fixed from some heuristic considerations
    # the user of this code is welcome to apply their own reasoning

    a, b = min(sizes), max(sizes)
    if a == b:
        sizes = len(sizes)*[30]
    else:
        if b <= 8*a:
            m, M = 15, 1 + int(20*b/a)
        elif b <= 16*a:
            m, M = 14, 1 + int(18*b/a)
        elif b <= 32*a:
            m, M = 13, 1 + int(9*b/a)
        elif b <= 64*a:
            m, M = 11, 1 + int(4.7*b/a)
        else:
            m, M = FONT_SIZE_MIN, FONT_SIZE_MAX

        sizes = [  int(((M - m )/(b - a))*( x - a ) + m )  for x in sizes ]

    # allow some vertical placement; the probability is defined by the user
    flips = randomFlips(len( words ), horizontalProbability )
    for i in range(len(sizes)):
        normalTokens.append( Token( words[i], sizes[i], 0 if flips[i] == 0 else 90 ) )

    return normalTokens



def drawWord(token, useColor = False):
    """
      gets an instance of Token class and draws the word it represents
      returns an image of the given word in the given font size
      the image is NOT cropped
    """

    font = ImageFont.truetype(FONT_NAME, token.fontSize)
    w, h = font.getsize(token.word)

    im = Image.new('RGBA', (w,h), color = None)
    draw = ImageDraw.Draw(im)
    if useColor == False:
        draw.text((0, 0), token.word, font = font)
    else:
        draw.text((0, 0), token.word, font = font, fill = token.color)

    if token.drawAngle != 0:
        im = im.rotate( token.drawAngle,  expand = 1)

    return im


def drawOnCanvas(normalTokens, canvas_size,theme=0):
    """
       given a list of tokens and a canvas size, we put the token images onto the canvas
       the places of each token on this canvas has already been determined during placeWords() call.

       Notice, that it is not required that the @place of each @token is inside the canvas;
       if necessary we may enlarge the canvas size to embrace these missing images
    """

    c_W,c_H = canvas_size        # the suggested canvas size, might change here

    # there can be some positions of words which fell out of the canvas
    # we first need to go through these exceptions (if any) and expand the canvas and (or) shift the coordinate's origin.

    X_min, Y_min = 0, 0

    for i, token in enumerate(normalTokens):
        if token.place == None:
            continue

        if X_min > token.place[0]:  X_min = token.place[0]
        if Y_min > token.place[1]:  Y_min = token.place[1]

    x_shift, y_shift = 0, 0
    if X_min < 0:   x_shift = -X_min
    if Y_min < 0:   y_shift = -Y_min

    X_max , Y_max = 0, 0
    for i, token in enumerate(normalTokens):
        if token.place == None:
            continue

        token.place = ( token.place[0] + x_shift, token.place[1] + y_shift )
        if X_max < token.place[0] + token.imgSize[0]:
            X_max = token.place[0] + token.imgSize[0]
        if Y_max < token.place[1] + token.imgSize[1]:
            Y_max = token.place[1] + token.imgSize[1]

    c_W = max(c_W, X_max)
    c_H = max(c_H, Y_max)

    im_canvas = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = None )
    im_canvas_white = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = (255,255,255,255) )

    # decide the background color with a coin flip; 0 -for white; 1 - for black (will need brigher colors)
    background = random.randint(0,0) # I've changed to be always white

    dd = ImageDraw.Draw(im_canvas)
    if background == 0: # white
        dd_white = ImageDraw.Draw(im_canvas_white)

    #COLOR THEMES (CUSTOMIZED)
    # add color to each word to be placed on canvas, pass on the background info as well
    if theme == 0:
        background = random.randint(0,1)
        CH.randomColors(normalTokens, background)
    elif theme == 1:
        background = 0
        CH.jetColors(normalTokens)
    elif theme == 2:
        background = 0
        CH.grayishRandomColors (normalTokens)
    elif theme == 3:
        background = background = 0
        CH.chooseFromFixedSchemes(normalTokens)
    elif theme >=4:
        background = background = 0
        CH.chooseFromCustom(normalTokens) # custom themes
        
        

    for i, token in enumerate(normalTokens):
        if token.place == None:
            #print('the word <' + token.word + '> was skipped' )
            continue

        font1 = ImageFont.truetype(FONT_NAME, token.fontSize)
        c = token.color

        if token.drawAngle != 0:
            # place vertically, since PIL does support drawing text in vertical orientation,
            # we first draw the token in a temporary image, the @im, then past that at the location of
            # the token on the canvas; this might introduce some rasterization for smaller fonts
            im = drawWord(token, useColor = True)
            im_canvas.paste(im,  token.place, im )
            if background == 0:
                im_canvas_white.paste(im,  token.place, im )
        else:
            dd.text( token.place, token.word, fill = c,  font = font1 )
            if background == 0:
                dd_white.text( token.place, token.word, fill = c,  font = font1 )


    margin_size = 10 # the border margin size
    box = im_canvas.getbbox()

    if background == 0:
        # white background
        im_canvas_1 = Image.new('RGBA', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (100,100,100,100)  )
        im_canvas_1.paste( im_canvas_white.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )
    else:
        # black background
        im_canvas_1 = Image.new('RGB', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (0,0,0)  )
        im_canvas_1.paste( im_canvas.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )

    return im_canvas_1

def createQuadTrees(normalTokens):
    """
        given a list of tokens we fill their quadTree attributes and cropped image size
    """
    for i, token in enumerate(normalTokens):
        im_tmp = drawWord(token)
        T = wordle_bbox.getQuadTree( im_tmp , QUADTREE_MINSIZE, QUADTREE_MINSIZE )
        T.compress()
        im_tmp = im_tmp.crop(im_tmp.getbbox())
        token.quadTree = T
        token.imgSize = im_tmp.size

def placeWords(normalTokens):
    """
      gets a list of tokens and their frequencies
      executes the placing strategy and
      returns canvas size, locations of upper-left corner of words and words' sizes
    """

    # 1. we first create the QuadTrees for all words and determine a size for the canvas
    word_img_path = [] # shows the path passed through the spiral before hitting a free space
    # create the quadTrees and collect sizes (width, height) of the cropped images of the words
    createQuadTrees(normalTokens)
    #2. We now find places for the words on our canvas
    c_W, c_H = 4000, 4000
    #c_W, c_H = 2000, 1000
    #c_W, c_H = 3000, 1500
    #c_W, c_H = 1000, 1000
    #3a. we start with the 1st word
    ups_and_downs = [ random.randint(0,20)%2  for i in range( len(normalTokens) )]
    for i, token in enumerate(normalTokens):
        a = 0.2                # the parameter of the spiral
        if ups_and_downs[i] == 1:
            # add some randomness to the placing strategy
            a = -a
        # determine a starting position on the canvas of this token, near half of the width of canvas
        w, h =   random.randint( int(0.3*c_W), int(0.7*c_W) ) ,  (c_H >> 1) - (token.imgSize[1] >> 1)
        if w < 0 or w >= c_W:
            w = c_W >> 1
        if h < 0 or h >= c_H:
            h = c_H >> 1
        if ups_and_downs[i] == 0:
            A = SP.Archimedian(a).generator
        else:
            A = SP.Rectangular(2, ups_and_downs[i]).generator
        dx0, dy0 = 0, 0
        place1 = (w, h)
        word_img_path.append( (w,h) )
        last_hit_index = 0 # we cache the index of last hit
        iter_ = 0
        start_countdown = False
        max_iter = 0
        for dx, dy in A:
            w, h = place1[0] + dx, place1[1] + dy
            if start_countdown == True:
                max_iter -= 1
                if max_iter == 0:
                    break
            else:
                iter_ += 1
            if ( w < 0 or w >= c_W or h < 0 or h > c_H ):
                #  the shape has fallen outside the canvas
                if start_countdown == False:
                    start_countdown = True
                    max_iter  = 1 + 10*iter_
            place1 = ( w, h )
            collision = False
            if last_hit_index < i:
                j = last_hit_index
                if normalTokens[j].place != None:
                    collision = wordle_bbox.collisionTest( token.quadTree, normalTokens[j].quadTree, place1, normalTokens[j].place, STAY_AWAY)
            if collision == False:
                # NO collision with the cached index
                for j in range( i ): # check for collisions with the rest of the tokens
                    if ((j != last_hit_index) and (normalTokens[j].place != None)):
                        if wordle_bbox.collisionTest(token.quadTree, normalTokens[j].quadTree, place1, normalTokens[j].place, STAY_AWAY) == True:
                            collision = True
                            last_hit_index = j
                            break # no need to check with the rest of the tokens, try a new position now
            if collision == False:
                if wordle_bbox.insideCanvas( token.quadTree , place1, (c_W, c_H) ) == True:
                    # at this point we have found a place inside the canvas where the current token has NO collision
                    # with the already placed tokens; The search has been completed.
                    token.place = place1
                    break   # breaks the spiral movement
                else:
                    if token.place == None:
                        # even though this place is outside the canvas, it is collision free and we
                        # store it in any case to ensure that the token will be placed
                        token.place = place1
    return c_W, c_H


def plot(tokens,freq,**kwargs):
    """
    Shows wordle in a matplotlib figure.
    themes: 0 random colors; 1 jet (heatmap); 2 grayish; 3 fixed colors.
    """
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    # args
    stretch = kwargs.get('strech',1.0)
    theme = kwargs.get('theme',2)
    vpos = kwargs.get('vertical',.1)
    hpos = kwargs.get('horizontal',1.0)
    verticalProbability = vpos    # the probability of placing some words vertically
    horizontalProbability = hpos - verticalProbability # the probability of placing some words horizontally
    normalTokens =  normalizeWordSize(tokens, freq, TOKENS_TO_USE, horizontalProbability)
    canvas_W, canvas_H = placeWords(normalTokens)
    wordle = drawOnCanvas(normalTokens, (canvas_W, canvas_H ),theme)
    # resize
    if stretch < 1:
        p = stretch * 100
        width = int( (wordle.width * p)/100)
        height = int((wordle.height * p)/100)
        wordle = wordle.resize((width,height), Image.BICUBIC) 
    temp = tempfile.TemporaryFile()
    try:
        wordle.save(temp.name + '.png')
        img=mpimg.imread(temp.name + '.png')
        imgplot = plt.imshow(img,interpolation='bessel')
        plt.axis('off')
        plt.show()
        os.remove(temp.name + '.png')
    finally:
        temp.close()

def show_image(tokens,freq,**kwargs):
    """
    Show wordle image in the default OS image viewer.
    """
    # args
    stretch = kwargs.get('strech',1.0)
    theme = kwargs.get('theme',2)
    vpos = kwargs.get('vertical',.1)
    hpos = kwargs.get('horizontal',1.0)
    verticalProbability = vpos    # the probability of placing some words vertically
    horizontalProbability = hpos - verticalProbability # the probability of placing some words horizontally
    normalTokens =  normalizeWordSize(tokens, freq, TOKENS_TO_USE, horizontalProbability)
    canvas_W, canvas_H = placeWords(normalTokens)
    wordle = drawOnCanvas(normalTokens, (canvas_W, canvas_H ),theme )
    # resize
    if stretch < 1:
        p = stretch * 100
        width = int((wordle.width * p)/100)
        height = int((wordle.height * p)/100)
        wordle = wordle.resize((width,height), Image.BICUBIC)
    wordle.show('Word cloud')
    

def save_image(tokens,freq,filename,**kwargs):
    """
    Show wordle image in the default OS image viewer.
    """
    # args
    stretch = kwargs.get('strech',1.0)
    theme = kwargs.get('theme',2)
    vpos = kwargs.get('vertical',.1)
    hpos = kwargs.get('horizontal',1.0)
    verticalProbability = vpos    # the probability of placing some words vertically
    horizontalProbability = hpos - verticalProbability # the probability of placing some words horizontally
    normalTokens =  normalizeWordSize(tokens, freq, TOKENS_TO_USE, horizontalProbability)
    canvas_W, canvas_H = placeWords(normalTokens)
    wordle = drawOnCanvas(normalTokens, (canvas_W, canvas_H ),theme)
    # resize
    if stretch < 1:
        p = stretch * 100
        width = int( (wordle.width * p)/100)
        height = int((wordle.height * p)/100)
        wordle = wordle.resize((width,height), Image.BICUBIC)
    wordle.save(filename)

    
    
    

