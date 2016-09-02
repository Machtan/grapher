# encoding: utf-8
# Created by Jakob Lautrup Nysom @ April 12th 2015
import sys
import os
import pygame
from simplegame import Game, Label

def tupadd(a, b):
    return a[0] + b[0], a[1] + b[1]

class Shape:
    def collidepoint(self, point):
        raise Exception("collidepoint not implemented for {}!".format(self))

    def draw(self, superpos, color, surface):
        raise Exception("draw not implemented for {}!".format(self))

class CompoundShape(Shape):
    def __init__(self, pos, shapes=[]):
        self.pos = pos
        self.shapes = shapes

    def collidepoint(self, point):
        any(shape.collidepoint(point) for shape in self.shapes)

    def draw(self, surface, color, superpos):
        pos = tupadd(superpos, self.pos)
        for shape in self.shapes:
            shape.draw(surface, color, pos)

class Rectangle(Shape):
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def collidepoint(self, pos):
        x, y = pos
        return x >= self.x and x <= self.x + self.w and y >= self.y and y <= self.y + self.h

    def draw(self, surface, color, superpos):
        pos = tupadd(superpos, (self.x, self.y))
        rect = pygame.Rect(pos, (self.w, self.h))
        pygame.draw.rect(surface, color, rect)

INSERT_CHARACTER = "|"

class EditableLabel:
    def __init__(self, text, pos, *args, **kwargs):
        self.padding = 3
        self.color = (255, 255, 255)
        self.fontsize = 14
        self.init_timeout = 0.5
        self.timeout = 1.0 / 15.0
        self.elapsed = 0
        self.repeating = False
        self.repeat_initialized = False
        self.curkey = None
        self.keydown = {
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_BACKSPACE: False,
            pygame.K_DELETE: False,
        }

        #print("Editable label: pos / padding - {} {}".format(pos, self.padding))
        labpos = (self.padding, self.padding)
        self.label = Label(text, labpos, *args, size=self.fontsize, **kwargs)
        self.label.add_listener(lambda x: self.redraw())
        self.focused = False
        size = tupadd(self.label.rect.size, ( self.padding * 2, self.padding * 2))
        self.rect = pygame.Rect(pos, size)
        self.listeners = []
        self.text = text
        self.pivot = len(text)


        self.redraw()

    def update(self, deltatime):
        if self.repeating:
            self.elapsed += deltatime
            if self.repeat_initialized:
                if self.elapsed >= self.timeout:
                    print("- Repeat!")
                    self.elapsed -= self.timeout
                    event = pygame.event.Event(pygame.KEYDOWN, key=self.curkey)
                    self.handle(event)
            elif self.elapsed >= self.init_timeout:
                print("repeat init: {}".format( self.curkey))
                self.elapsed -= self.init_timeout
                self.repeat_initialized = True
                event = pygame.event.Event(pygame.KEYDOWN, key=self.curkey)
                self.handle(event)

    def add_listener(self, listener):
        """Adds a listener to be given the label when its contents update"""
        self.listeners.append(listener)

    def redraw(self):
        print("Redrawing editable label")
        size = tupadd(self.label.rect.size, ( self.padding * 2, self.padding * 2))
        self.rect.size = size
        self.image = pygame.Surface(size)
        self.image.convert()
        self.image.fill( self.color)
        self.label.render( self.image )
        for listener in self.listeners:
            listener(self)

    def get_text(self):
        return self.label.text

    def move(self, amount):
        self.rect.topleft = tupadd( self.rect.topleft, amount)
        self.label.move(amount)

    def render(self, surface):
        surface.blit( self.image, self.rect.topleft)

    def set_focused(self):
        if not self.focused:
            print("Focused!")
            self.pivot = len(self.text)
            self.focused = True
            self.update_label()
            self.label.redraw()

    def update_label(self):
        self.label.text = self.text[:self.pivot] + INSERT_CHARACTER + self.text[self.pivot:]

    def set_unfocused(self):
        if self.focused:
            print("Unfocused!")
            self.focused = False
            self.label.text = self.text
            self.label.redraw()

    def handle(self, event):
        if self.focused:
            if event.type == pygame.KEYDOWN:
                if event.key != self.curkey:
                    self.repeating = False
                    self.repeat_initialized = False
                    self.elapsed = 0
                self.curkey = event.key
                if event.key in self.keydown:
                    self.keydown[event.key] = True

                if event.key == pygame.K_LEFT:
                    self.repeating = True
                    self.pivot = max(0, self.pivot - 1)
                elif event.key == pygame.K_RIGHT:
                    self.repeating = True
                    self.pivot = min(len(self.text), self.pivot + 1)
                elif event.key == pygame.K_UP:
                    pass
                elif event.key == pygame.K_DOWN:
                    pass
                elif event.key == pygame.K_RETURN:
                    self.set_unfocused()
                elif event.key == pygame.K_ESCAPE:
                    self.set_unfocused()
                elif event.key == pygame.K_DELETE:
                    self.repeating = True
                    if self.pivot != len(self.text):
                        self.text = self.text[:self.pivot] + self.text[self.pivot + 1:]
                elif event.key == pygame.K_BACKSPACE:
                    self.repeating = True
                    if self.pivot != 0:
                        self.text = self.text[:self.pivot-1] + self.text[ self.pivot:]
                        self.pivot -= 1
                elif event.unicode:
                    self.text = self.text[:self.pivot] + event.unicode + self.text[self.pivot:]
                    self.pivot += 1

                if self.focused: # Ensure that this hasn't changed
                    self.update_label()
                self.label.redraw()
                    #print(event)

            elif event.type == pygame.KEYUP:
                if event.key == self.curkey:
                    self.repeating = False
                    self.repeat_initialized = False
                    self.elapsed - 0
                if event.key in self.keydown:
                    self.keydown[event.key] = False

class Circle(Shape):
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.r = radius

    def collidepoint(self, pos):
        xdist = pos[0] - self.x
        ydist = pos[1] - self.y
        return (xdist ** 2 + ydist ** 2) <= self.r ** 2

    def draw(self, surface, color, superpos):
        pos = tupadd(superpos, (self.x, self.y))

class Item:
    def __init__(self, parent, name, surf, size, constructorfunc):
        self.parent = parent
        self.dragging = False

    def handle_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pass
            #if self.rect.
        elif event.type == pygame.MOUSEBUTTONUP:
            pass
        elif event.type == pygame.MOUSEMOTION:
            pass

class ItemSelector:
    def __init__(self, pos):
        self.padding = 5
        self.color = (220, 220, 220)
        self.height = self.padding * 2
        self.width = self.padding * 2
        self.items = []

    def redraw(self):
        pass

    def handle_mouse(self, event):
        for item in items:
            item.handle_mouse(event)

    def add_item(self, name, surf, constructorfunc):
        pass

    def render(self, surf):
        pass

class Node:
    def __init__(self, pos, text=""):
        self.padding = 2
        self.dragging = False
        self.color = (100, 100, 100)
        #print("Node pos:")
        labpos = ( self.padding, self.padding)
        self.label = EditableLabel(text, labpos)
        self.label.add_listener(lambda _: self.redraw())
        size = tupadd(self.label.rect.size, (self.padding * 2, self.padding * 2))
        self.rect = pygame.Rect(pos, size)

        self.redraw()

    def update(self, deltatime):
        self.label.update(deltatime)

    def redraw(self):
        self.labrect = pygame.Rect(tupadd( self.rect.topleft,
            ( self.padding, self.padding)), self.label.rect.size)
        size = tupadd(self.label.rect.size, (self.padding * 2, self.padding * 2))
        self.rect.size = size

        self.image = pygame.Surface(size)
        self.image.convert()
        self.image.fill(self.color)
        self.label.render( self.image )

    def handle(self, event):
        """delegate the event to the label, probably"""
        self.label.handle(event)

    def move(self, amount):
        self.rect = self.rect.move(amount)
        self.labrect = self.labrect.move(amount)

    def render(self, surface):
        surface.blit( self.image, self.rect.topleft)

    def handle_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # LEFT
                if self.labrect.collidepoint(event.pos):
                    print("Inside label!")
                    # Start editing
                    self.label.set_focused()
                else:
                    self.label.set_unfocused()
            elif event.button == 3: # Right click inside the label
                if self.rect.collidepoint(event.pos):
                    #print("Node button: {}".format(event.button))
                    self.dragging = True
                    self.label.set_unfocused()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.move(event.rel)

def main(args=sys.argv[1:]):
    game = Game()

    n1 = Node((10, 10))
    n2 = Node((100, 20), "Hello world")

    game.add(n1, n2)

    game.run()

if __name__ == '__main__':
    main()