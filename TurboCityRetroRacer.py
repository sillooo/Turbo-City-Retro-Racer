import pygame, sys, math, time

pygame.init()

WIDTH, HEIGHT = 900, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🏁 Turbo City: Retro Racer")

BLACK=(10,10,20)
CYAN=(0,255,255)
MAGENTA=(255,0,255)
YELLOW=(255,255,100)
ROAD_COLOR=(60,60,80)
BOUNDARY_COLOR=(200,50,255)
FINISH_COLOR=(255,255,100)
OFFROAD_COLOR=(15,15,25)
FINISH_SHIFT = 50

TITLE_FONT=pygame.font.SysFont("Consolas",64,bold=True)
MENU_FONT=pygame.font.SysFont("Consolas",36)
INFO_FONT=pygame.font.SysFont("Consolas",22)

STATE_MENU,STATE_TRACK_SELECT,STATE_GAME,STATE_INSTR="menu","track","game","instructions"

car_img=pygame.Surface((60,30),pygame.SRCALPHA)
pygame.draw.polygon(car_img,CYAN,[(60,15),(10,0),(0,15),(10,30)])

class Car:
    def __init__(self,x,y,angle=0):
        self.x=x; self.y=y; self.angle=angle
        self.speed=0; self.max_speed=8
        self.accel=0.25; self.turn_speed=4
        self.friction=0.03
    def reset(self,pos,angle=0):
        self.x,self.y=pos; self.angle=angle
        self.speed=0
    def move_input(self,keys):
        if keys[pygame.K_UP]: self.speed+=self.accel
        elif keys[pygame.K_DOWN]: self.speed-=self.accel
        else:
            if self.speed>0:self.speed-=self.friction
            elif self.speed<0:self.speed+=self.friction
        self.speed=max(-5,min(self.speed,self.max_speed))
        speed_frac = (self.speed / self.max_speed) if self.max_speed else 0
        if keys[pygame.K_LEFT]: self.angle+=self.turn_speed*speed_frac
        if keys[pygame.K_RIGHT]: self.angle-=self.turn_speed*speed_frac
        rad=math.radians(self.angle)
        return self.x+math.cos(rad)*self.speed,self.y-math.sin(rad)*self.speed
    def draw(self,win):
        r=pygame.transform.rotate(car_img,self.angle)
        win.blit(r,r.get_rect(center=(self.x,self.y)))

TRACKS={
"City Circuit":{
"inner_walls":[((150,450),(750,450)),((750,450),(750,150)),((750,150),(150,150)),((150,150),(150,450))],
"outer_walls":[((50,550),(850,550)),((850,550),(850,50)),((850,50),(50,50)),((50,50),(50,550))],
"start_before":(380,520),"finish":((450,500),(450,400))},
"Coastal Dash":{
"inner_walls":[((200,500),(700,500)),((700,500),(800,400)),((800,400),(700,250)),
((700,250),(200,250)),((200,250),(100,400)),((100,400),(200,500))],
"outer_walls":[((100,600),(800,600)),((800,600),(900,400)),((900,400),(800,200)),
((800,200),(100,200)),((100,200),(0,400)),((0,400),(100,600))],
"start_before":(420,570),"finish":((450,550),(450,450))}}

def point_near_line(p,a,b,d):
    px,py=p; ax,ay=a; bx,by=b
    l=math.hypot(bx-ax,by-ay)
    if l<1:return False
    u=max(0,min(1,((px-ax)*(bx-ax)+(py-ay)*(by-ay))/l**2))
    ix=ax+u*(bx-ax); iy=ay+u*(by-ay)
    return math.hypot(px-ix,py-iy)<d

def crossed_finish(car,finish):
    a,b=finish
    fa = (a[0], a[1] + FINISH_SHIFT)
    fb = (b[0], b[1] + FINISH_SHIFT)
    return point_near_line((car.x,car.y),fa,fb,10)

def collides(x,y,walls):
    for s in walls:
        if point_near_line((x,y),s[0],s[1],5):return True
    return False

def draw_track(name):
    WIN.fill(OFFROAD_COLOR)
    
    outer_points = []
    for wall in TRACKS[name]["outer_walls"]:
        outer_points.append(wall[0])
    
    inner_points = []
    for wall in TRACKS[name]["inner_walls"]:
        inner_points.append(wall[0])
    
    if len(outer_points) > 2:
        pygame.draw.polygon(WIN, ROAD_COLOR, outer_points)
    
    if len(inner_points) > 2:
        pygame.draw.polygon(WIN, OFFROAD_COLOR, inner_points)
    
    for s in TRACKS[name]["inner_walls"]: 
        pygame.draw.line(WIN,BOUNDARY_COLOR,s[0],s[1],4)
    
    for s in TRACKS[name]["outer_walls"]: 
        pygame.draw.line(WIN,BOUNDARY_COLOR,s[0],s[1],4)
    
    finish = TRACKS[name]["finish"]
    finish_width = 10
    offset = finish_width / 2.0
    f0 = (finish[0][0], finish[0][1] + offset + FINISH_SHIFT)
    f1 = (finish[1][0], finish[1][1] + offset + FINISH_SHIFT)
    pygame.draw.line(WIN,FINISH_COLOR,(int(f0[0]),int(f0[1])),(int(f1[0]),int(f1[1])),finish_width)

def draw_hud(car,ct,last,best,started):
    pygame.draw.rect(WIN,(20,20,40),(0,0,WIDTH,40))
    t=f"Time: {ct:.2f}s" if started else "Time: ---"
    l=f"Last: {last:.2f}s" if last else "Last: ---"
    b=f"Best: {best:.2f}s" if best<float('inf') else "Best: ---"
    time_surf = INFO_FONT.render(t, True, CYAN)
    WIN.blit(time_surf, (20,10))
    speed_x = 20 + time_surf.get_width() + 20
    speed_text = f"Speed: {car.speed:.1f}"
    speed_surf = INFO_FONT.render(speed_text, True, YELLOW)
    WIN.blit(speed_surf, (speed_x, 10))
    bar_w = 120
    bar_h = 10
    bar_x = speed_x + speed_surf.get_width() + 12
    bar_y = 15
    pygame.draw.rect(WIN, (40,40,60), (bar_x, bar_y, bar_w, bar_h)) 
    ratio = 0.0
    if car.max_speed != 0:
        ratio = max(-1.0, min(1.0, car.speed / car.max_speed))
    center_x = bar_x + bar_w // 2
    fill_w = int(abs(ratio) * (bar_w // 2))
    if ratio > 0:
        pygame.draw.rect(WIN, YELLOW, (center_x, bar_y, fill_w, bar_h))
    elif ratio < 0:
        pygame.draw.rect(WIN, MAGENTA, (center_x - fill_w, bar_y, fill_w, bar_h))
    last_best_surf = INFO_FONT.render(f"{l} | {b}", True, CYAN)
    lb_x = WIDTH - 20 - last_best_surf.get_width()
    WIN.blit(last_best_surf, (lb_x, 10))

def game_loop(track):
    c=pygame.time.Clock()
    data=TRACKS[track]
    car=Car(*data["start_before"])
    best=float('inf'); last=0; running=True
    race_started=False; start_time=0; last_cross=0
    while running:
        c.tick(60); keys=pygame.key.get_pressed()
        for e in pygame.event.get():
            if e.type==pygame.QUIT:pygame.quit();sys.exit()
            if keys[pygame.K_b]or keys[pygame.K_ESCAPE]:return
            if keys[pygame.K_r]: car.reset(data["start_before"]); race_started=False; last=0
        nx,ny=car.move_input(keys)
        if not collides(nx,ny,data["inner_walls"]+data["outer_walls"]): car.x,car.y=nx,ny
        else: car.speed*=-0.3
        if crossed_finish(car,data["finish"]) and time.time()-last_cross>3:
            if not race_started: race_started=True; start_time=time.time()
            else:
                lap=time.time()-start_time; last=lap
                if lap<best: best=lap
                start_time=time.time()
            last_cross=time.time()
        draw_track(track); car.draw(WIN)
        current=(time.time()-start_time) if race_started else 0
        draw_hud(car,current,last,best,race_started)
        pygame.display.update()

def draw_menu(sel):
    WIN.fill(BLACK)
    t=TITLE_FONT.render("Turbo City: Retro Racer",True,CYAN)
    WIN.blit(t,(WIDTH//2-t.get_width()//2,150))
    items=["Start Game","Instructions","Quit"]
    for i,tx in enumerate(items):
        col=YELLOW if i==sel else MAGENTA
        lab=MENU_FONT.render(tx,True,col)
        WIN.blit(lab,(WIDTH//2-lab.get_width()//2,320+i*60))
    pygame.display.update()

def draw_instr():
    WIN.fill(BLACK)
    t=TITLE_FONT.render("Instructions",True,MAGENTA)
    WIN.blit(t,(WIDTH//2-t.get_width()//2,100))
    lines=[
        "Ud/Down Arrow Keys Move | Left/Right Arrow Keys Steer",
        "R Reset | B Return to Menu",
        "Timer starts AFTER finish line.",
    ]
    for i,l in enumerate(lines):
        WIN.blit(INFO_FONT.render(l,True,CYAN),(WIDTH//2-INFO_FONT.size(l)[0]//2,250+i*30))
    pygame.display.update()

def track_select():
    sel=0; names=list(TRACKS.keys())
    while True:
        WIN.fill(BLACK)
        t=TITLE_FONT.render("Select Track",True,CYAN)
        WIN.blit(t,(WIDTH//2-t.get_width()//2,120))
        for i,n in enumerate(names):
            col=YELLOW if i==sel else MAGENTA
            lab=MENU_FONT.render(n,True,col)
            WIN.blit(lab,(WIDTH//2-lab.get_width()//2,300+i*60))
        pygame.display.update()
        for e in pygame.event.get():
            if e.type==pygame.QUIT:pygame.quit();sys.exit()
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_UP: sel=(sel-1)%len(names)
                elif e.key==pygame.K_DOWN: sel=(sel+1)%len(names)
                elif e.key==pygame.K_RETURN: return names[sel]
                elif e.key==pygame.K_b: return None

def main():
    state=STATE_MENU; sel=0; clk=pygame.time.Clock()
    while True:
        clk.tick(60)
        if state==STATE_MENU:
            draw_menu(sel)
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit();sys.exit()
                elif e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_UP: sel=(sel-1)%3
                    elif e.key==pygame.K_DOWN: sel=(sel+1)%3
                    elif e.key==pygame.K_RETURN:
                        if sel==0: state=STATE_TRACK_SELECT
                        elif sel==1: state=STATE_INSTR
                        elif sel==2: pygame.quit();sys.exit()
        elif state==STATE_INSTR:
            draw_instr()
            for e in pygame.event.get():
                if e.type==pygame.KEYDOWN and e.key==pygame.K_b: state=STATE_MENU
        elif state==STATE_TRACK_SELECT:
            ch=track_select()
            if ch: game_loop(ch)
            state=STATE_MENU
def _center_track_vertical(name):
    pts = []
    for seg in TRACKS[name]["inner_walls"] + TRACKS[name]["outer_walls"]:
        pts.append(seg[0]); pts.append(seg[1])
    ys = [p[1] for p in pts]
    if not ys: return
    track_center = (min(ys) + max(ys)) / 2.0
    target_center = HEIGHT / 2.0
    dy = target_center - track_center
    def shift_pt(p):
        return (int(p[0]), int(p[1] + dy))
    for key in ("inner_walls","outer_walls"):
        TRACKS[name][key] = [(shift_pt(a), shift_pt(b)) for (a,b) in TRACKS[name][key]]
    if "start_before" in TRACKS[name]:
        sb = TRACKS[name]["start_before"]; TRACKS[name]["start_before"] = shift_pt(sb)
    if "finish" in TRACKS[name]:
        f0,f1 = TRACKS[name]["finish"]
        TRACKS[name]["finish"] = (shift_pt(f0), shift_pt(f1))
_center_track_vertical("Coastal Dash")

if __name__=="__main__": main()