"""Sarpele padurii: versiune Android / Kivy, fara dependenta Pygame."""
import math
import random
from pathlib import Path

from kivy.config import Config
Config.set('graphics', 'width', '540')
Config.set('graphics', 'height', '760')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Rectangle, Ellipse, Line, PushMatrix, PopMatrix, Translate, Scale, StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.uix.widget import Widget

ROOT = Path(__file__).resolve().parent
W, H, GROUND = 540, 760, 700


class ForestGame(Widget):
    def __init__(self, record_path, **kwargs):
        super().__init__(**kwargs)
        self.record_path = record_path
        try:
            self.best = int(record_path.read_text())
        except (OSError, ValueError):
            self.best = 0
        self.textures = {}
        for file in (ROOT / 'assets').glob('*.png'):
            self.textures[file.stem] = CoreImage(str(file)).texture
        self.text_cache = {}
        rng = random.Random(731)
        self.particles = [(rng.randrange(W), rng.randrange(GROUND), rng.uniform(.6, 1.5)) for _ in range(110)]
        self.reset()
        Window.bind(on_key_down=self.key)
        Clock.schedule_interval(self.update, 1 / 60)

    def reset(self):
        self.state = 'ready'
        self.snake_y, self.velocity = 330., 0.
        self.score, self.timer, self.elapsed, self.time = 0, 0., 0., 0.
        self.snow = 0.
        self.trees = []
        self.paused = False

    def key(self, window, key, *args):
        if key in (32, 273):
            self.jump()
            return True
        if key == 114:
            self.reset()
            return True
        if key in (27, 112):
            self.paused = not self.paused
            return True

    def on_touch_down(self, touch):
        scale = min(self.width / W, self.height / H)
        ox, oy = self.x + (self.width - W * scale) / 2, self.y + (self.height - H * scale) / 2
        xx, yy = (touch.x - ox) / scale, H - (touch.y - oy) / scale
        if not (0 <= xx <= W and 0 <= yy <= H):
            return False
        if xx > 460 and yy < 65:
            self.paused = not self.paused
        else:
            self.jump()
        return True

    def jump(self):
        if self.paused:
            self.paused = False
            return
        if self.state == 'dead':
            self.reset()
        self.state = 'playing'
        self.velocity = -340

    def save_record(self):
        if self.score > self.best:
            self.best = self.score
            self.record_path.parent.mkdir(parents=True, exist_ok=True)
            self.record_path.write_text(str(self.best))

    def update(self, dt):
        dt = min(dt, .035)
        if not self.paused:
            self.time += dt
            if self.state == 'playing':
                self.elapsed += dt
                self.velocity += 950 * dt
                self.snake_y += self.velocity * dt
                self.timer -= dt
                if self.timer <= 0:
                    center = random.choice((220, 280, 340, 400, 460))
                    self.trees.append({'x': 560., 'center': center, 'passed': False})
                    self.timer = 1.65
                for tree in self.trees:
                    tree['x'] -= (175 + min(self.score * 2, 55)) * dt
                    if not tree['passed'] and tree['x'] + 88 < 145:
                        tree['passed'] = True
                        self.score += 1
                    if tree['x'] < 160 and tree['x'] + 88 > 130:
                        if self.snake_y - 14 < tree['center'] - 112 or self.snake_y + 14 > tree['center'] + 112:
                            self.state = 'dead'
                self.trees = [tree for tree in self.trees if tree['x'] > -100]
                if self.snake_y < 16 or self.snake_y > GROUND - 15:
                    self.state = 'dead'
                self.snow = max(0., min(1., self.snow + dt * (.085 if self.weather() == 'NINSOARE' else -.055)))
                if self.state == 'dead':
                    self.save_record()
            elif self.state == 'ready':
                self.snake_y = 330 + math.sin(self.time * 3) * 10
        self.render()

    def weather(self):
        phase = self.elapsed % 44
        return 'SENIN' if phase < 8 or phase >= 36 else ('PLOAIE' if phase < 20 else 'NINSOARE')

    def color(self, rgb, alpha=1):
        Color(*(v / 255 for v in rgb), alpha)

    def rect(self, x, y, w, h, color, alpha=1):
        self.color(color, alpha)
        Rectangle(pos=(x, H-y-h), size=(w, h))

    def ellipse(self, x, y, w, h, color, alpha=1):
        self.color(color, alpha)
        Ellipse(pos=(x, H-y-h), size=(w, h))

    def line(self, points, color, width=1):
        self.color(color)
        Line(points=[v for x,y in points for v in (x,H-y)], width=width)

    def image(self, name, x, y, width, height, alpha=1):
        Color(1,1,1,alpha)
        Rectangle(texture=self.textures[name], pos=(x,H-y-height), size=(width,height))

    def text(self, text, y, size=22):
        key = (text, size)
        if key not in self.text_cache:
            label = CoreLabel(text=text, font_size=size, bold=True)
            label.refresh()
            if len(self.text_cache) > 100:
                self.text_cache.clear()
            self.text_cache[key] = label.texture
        texture = self.text_cache[key]
        Color(1,1,1,1)
        Rectangle(texture=texture, pos=((W-texture.width)/2, H-y-texture.height), size=texture.size)

    def render(self):
        self.canvas.clear()
        with self.canvas:
            self.color((20,15,34))
            Rectangle(pos=self.pos,size=self.size)
            PushMatrix()
            scale = min(self.width/W, self.height/H)
            Translate(self.x+(self.width-W*scale)/2, self.y+(self.height-H*scale)/2)
            Scale(scale,scale,1)
            StencilPush()
            Rectangle(pos=(0,0),size=(W,H))
            StencilUse()
            self.image('forest',0,0,W,H)
            if self.snow:
                self.image('forest_snow',0,0,W,H,self.snow)
            for tree in self.trees:
                self.image('tree_'+str(tree['center']),tree['x'],0,88,GROUND)
                if self.snow:
                    self.image('snow_'+str(tree['center']),tree['x'],0,88,GROUND,self.snow)
            offset = (self.time*80)%W
            self.image('ground',-offset,GROUND,W,60)
            self.image('ground',W-offset,GROUND,W,60)
            if self.snow:
                self.rect(0,GROUND,W,4+self.snow*36,(223,235,248),self.snow)
                for i in range(19):
                    self.ellipse((i*33-offset)%(W+40)-20,GROUND-2,45,12,(239,246,255),self.snow)
            for i in range(10,0,-1):
                radius = max(3,12-i//2)
                xx, yy = 145-i*7, self.snake_y+math.sin(self.time*9-i*.55)*i*.75
                self.ellipse(xx-radius,yy-radius,radius*2,radius*2,(104,200,102))
            self.ellipse(129,self.snake_y-15,34,30,(149,231,116))
            self.ellipse(145,self.snake_y-13,12,12,(255,250,203))
            self.ellipse(150,self.snake_y-10,6,6,(28,34,45))
            self.line([(160,self.snake_y+5),(171,self.snake_y+5),(175,self.snake_y+1)],(236,123,161))
            self.line([(171,self.snake_y+5),(175,self.snake_y+9)],(236,123,161))
            weather = self.weather()
            if weather != 'SENIN':
                self.rect(0,0,W,H,(34,45,73),.12)
                for px,py,speed in self.particles:
                    if weather == 'PLOAIE':
                        xx,yy = (px-self.time*150*speed)%(W+20),(py+self.time*610*speed)%GROUND
                        self.line([(xx,yy),(xx-5,yy+15*speed)],(148,178,213),.7)
                    else:
                        xx = (px+self.time*24*speed+math.sin(self.time*1.5+py)*15)%W
                        yy = (py+self.time*65*speed)%GROUND
                        self.ellipse(xx,yy,3*speed,3*speed,(235,243,255))
            self.text(str(self.score),25,46)
            self.text('RECORD  '+str(self.best),83,18)
            self.text(weather,112,17)
            self.rect(472,14,54,48,(40,30,65),.85)
            self.rect(489,27,6,22,(235,230,250))
            self.rect(502,27,6,22,(235,230,250))
            if self.state in ('ready','dead') or self.paused:
                self.rect(30,430,480,165,(26,20,49),.92)
                self.text('PAUZA' if self.paused else ('SARPELE PADURII' if self.state=='ready' else 'JOC TERMINAT'),450,27)
                self.text('Atinge ecranul pentru a continua' if self.paused else 'Atinge ecranul pentru a sari',505,21)
                self.text('Strecoara-te printre copaci!',548,19)
            StencilUnUse()
            Rectangle(pos=(0,0),size=(W,H))
            StencilPop()
            PopMatrix()


class ForestApp(App):
    title = 'Sarpele padurii'

    def build(self):
        Window.clearcolor = (.08,.05,.13,1)
        self.game = ForestGame(Path(self.user_data_dir)/'record.txt')
        return self.game

    def on_pause(self):
        self.game.paused = True
        self.game.save_record()
        return True

    def on_stop(self):
        self.game.save_record()


if __name__ == '__main__':
    ForestApp().run()
