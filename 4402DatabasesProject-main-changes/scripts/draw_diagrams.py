"""Render report diagrams as PNG and editable SVG (requires Pillow)."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[1]/'docs/diagrams'
W,H=2400,1800
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
# On other systems, set FONT and BOLD to installed TrueType font paths.
INK='#243a36'; GREEN='#315e50'; LINE='#63796e'; PAPER='#ffffff'; MUTED='#586960'

class Canvas:
 def __init__(self):
  self.im=Image.new('RGB',(W,H),PAPER); self.d=ImageDraw.Draw(self.im)
  self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>']
 def rect(self,x,y,w,h,fill,stroke=None):
  self.d.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke,width=3)
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke or fill}" stroke-width="3"/>')
 def text(self,x,y,s,size=28,bold=False,color=INK,center=False):
  font=ImageFont.truetype(BOLD if bold else FONT,size)
  width=self.d.textlength(s,font=font)
  if center:x-=width/2
  self.d.text((x,y),s,font=font,fill=color)
  self.svg.append(f'<text x="{x}" y="{y+size*.92}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(s)}</text>')
 def line(self,pts,arrow=False):
  self.d.line(pts,fill=LINE,width=4)
  self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="'+LINE+'" stroke-width="4"/>')
  if arrow:
   import math
   x,y=pts[-1]; a=math.atan2(y-pts[-2][1],x-pts[-2][0])
   self.line([(x-20*math.cos(a-.45),y-20*math.sin(a-.45)),(x,y),(x-20*math.cos(a+.45),y-20*math.sin(a+.45))])
 def diamond(self,x,y,name):
  pts=[(x-126,y),(x,y-54),(x+126,y),(x,y+54)]
  self.d.polygon(pts,fill='#f4f1e8',outline=LINE,width=3)
  self.svg.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in pts)+'" fill="#f4f1e8" stroke="'+LINE+'" stroke-width="3"/>')
  self.text(x,y-17,name,25,True,center=True)
 def tag(self,x,y,s):
  font=ImageFont.truetype(FONT,25); width=self.d.textlength(s,font=font)
  self.rect(x-8,y-3,width+16,36,PAPER); self.text(x,y,s,25)
 def box(self,x,y,w,name,rows):
  h=76+len(rows)*43+16
  self.rect(x,y,w,h,'#f7faf7',LINE); self.rect(x,y,w,66,GREEN)
  self.text(x+22,y+15,name,31,True,'#ffffff')
  for i,row in enumerate(rows):self.text(x+22,y+82+i*43,row,26)
 def save(self,name):
  OUT.mkdir(exist_ok=True,parents=True)
  self.im.save(OUT/(name+'.png'),dpi=(220,220))
  (OUT/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>']))

def base(title,subtitle):
 c=Canvas(); c.text(80,50,'VICIOUS BISCUIT  /  CSC4402',25,True,GREEN)
 c.text(80,100,title,54,True); c.text(80,175,subtitle,28,color=MUTED); return c

# Arrangement avoids crossed relationship lines. Counts denote participation
# by an individual entity instance in the adjacent relationship.
c=base('Entity–relationship diagram','Compact E-R notation: entity boxes contain attributes; diamonds name relationships.')
c.line([(620,380),(1610,380)]); c.diamond(1115,380,'owns'); c.tag(650,337,'0..N'); c.tag(1510,337,'1')
c.line([(620,450),(830,690)]); c.diamond(725,570,'places'); c.tag(640,470,'0..N'); c.tag(765,650,'0..1')
c.line([(620,810),(830,810)]); c.diamond(725,810,'handles'); c.tag(633,748,'0..N'); c.tag(796,748,'1')
c.line([(1390,690),(1610,560)]); c.diamond(1500,625,'generates'); c.tag(1410,710,'0..2'); c.tag(1585,575,'1')
c.line([(1390,940),(1610,1130)]); c.diamond(1500,1035,'contains'); c.tag(1405,960,'1..N'); c.tag(1590,1070,'1')
c.line([(620,1310),(1610,1310)]); c.diamond(1115,1310,'appears in'); c.tag(650,1262,'0..N'); c.tag(1520,1262,'1')
c.box(80,290,540,'Customer',['customer_id [PK]','name'])
c.box(80,720,540,'Employee',['employee_id [PK]','name'])
c.box(80,1110,540,'MenuItem',['menu_item_id [PK]','name','category','price_cents','available'])
c.box(830,650,560,'CustomerOrder',['order_id [PK]','created_at','subtotal_cents','discount_cents','paid_cents'])
c.box(1610,290,690,'RewardsTransaction',['transaction_id [PK]','points_change','transaction_type','created_at'])
c.box(1610,1110,690,'OrderItem',['order + menu item [composite PK]','quantity','unit_price_cents'])
c.text(80,1515,'HOW TO READ',25,True,GREEN)
c.text(80,1560,'A count near an entity gives how many relationship instances that entity may participate in.',28)
c.text(80,1605,'Example: a customer places 0..N orders; an order is placed by 0..1 customer (guests are allowed).',28)
c.text(80,1650,'Each order has 1..N line items. Rewards belong to the same member as their order; guest orders earn none.',28)
c.text(80,1695,'An order generates at most one earn entry and one redeem entry. Minimum one line item is enforced by checkout.',28)
c.save('entity-relationship')

c=base('Relational schema','Six relations with primary keys, foreign keys, data types, and key constraints.')
# Arrows point from referencing relation to referenced relation.
c.line([(830,745),(700,745),(700,390),(620,390)],True); c.tag(715,485,'FK 1')
c.line([(830,788),(620,788)],True); c.tag(670,745,'FK 2')
c.line([(1610,405),(1460,405),(1460,250),(350,250),(350,290)],True); c.tag(1020,212,'FK 3')
c.line([(1610,540),(1480,540),(1480,690),(1390,690)],True); c.tag(1485,585,'FK 4')
c.line([(1610,1190),(1480,1190),(1480,995),(1390,995)],True); c.tag(1485,1110,'FK 5')
c.line([(1610,1310),(620,1310)],True); c.tag(1060,1265,'FK 6')
c.box(80,290,540,'Customer',['PK  customer_id : INTEGER','     name : TEXT'])
c.box(80,720,540,'Employee',['PK  employee_id : INTEGER','     name : TEXT'])
c.box(80,1110,540,'MenuItem',['PK  menu_item_id : INTEGER','     name : TEXT','     category : TEXT','     price_cents : INTEGER','     available : INTEGER'])
c.box(830,620,560,'CustomerOrder',['PK  order_id : INTEGER','FK  customer_id : INTEGER *','FK  employee_id : INTEGER','     created_at : TEXT','     subtotal_cents : INTEGER','     discount_cents : INTEGER','     paid_cents : INTEGER'])
c.box(1610,290,690,'RewardsTransaction',['PK  transaction_id : INTEGER','FK  customer_id : INTEGER','FK  order_id : INTEGER','     points_change : INTEGER','     transaction_type : TEXT','     created_at : TEXT'])
c.box(1610,1110,690,'OrderItem',['PK, FK  order_id : INTEGER','PK, FK  menu_item_id : INTEGER','        quantity : INTEGER','        unit_price_cents : INTEGER'])
c.text(80,1490,'KEYS & REFERENCES',25,True,GREEN)
notes=[
'PK = primary key; FK = foreign key. * customer_id is nullable only in CustomerOrder; all other fields are required.',
'FK 1: CustomerOrder.customer_id → Customer.customer_id.  FK 2: CustomerOrder.employee_id → Employee.employee_id.',
'FK 3: RewardsTransaction.customer_id → Customer.customer_id.',
'FK 4 (composite): RewardsTransaction.(order_id, customer_id) → CustomerOrder.(order_id, customer_id).',
'FK 5: OrderItem.order_id → CustomerOrder.order_id.  FK 6: OrderItem.menu_item_id → MenuItem.menu_item_id.',
'OrderItem PK: (order_id, menu_item_id).  UNIQUE: CustomerOrder(order_id, customer_id); RewardsTransaction(order_id, transaction_type).',
'Money is stored in cents. Detailed CHECK constraints and defaults are defined in sql/schema.sql.'
]
for i,n in enumerate(notes):c.text(80,1535+i*35,n,25)
c.save('relational-schema')
print('Created two PNG diagrams and two editable SVG diagrams in',OUT)
