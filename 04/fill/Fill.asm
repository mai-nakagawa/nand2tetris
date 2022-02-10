// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed.
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

(LOOP)
  @10
  D=A
  @SCREEN
  D=D+A
  @i
  M=D
  @KBD
  D=M
  @FILL_WHITE
  D;JEQ
  @FILL_BLACK
  D;JNE
(FILL_BLACK)
  @i
  M=M-1
  A=M
  M=-1
  D=M
  @SCREEN
  D=D-M
  @LOOP
  D;JEQ
  @FILL_BLACK
  0;JMP
(FILL_WHITE)
  @i
  M=M-1
  A=M
  M=0
  D=M
  @SCREEN
  D=D-M
  @LOOP
  D;JEQ
  @FILL_WHITE
  0;JMP
