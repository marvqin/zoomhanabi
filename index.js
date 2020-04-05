import express from "express";
import http from "http";
import socket from "socket.io";
import path from "path";
// var express = require('express');
var app = express();
var server = http.createServer(app);
var io = socket(server);
// var io = require('socket.io')(http);

import {ServerRoom} from "./modules/Room.js"
// import {Server} from "./modules/Server.js"

// var ServerRoom = require('./Room').ServerRoom;
// var Player = require('./Player').Player;



app.get('/', function(req, res){
  // console.log(path.resolve());
  res.sendFile(path.resolve() + '/index.html');
});
app.use(express.static(path.resolve() + '/'));
var ss = new ServerRoom(io);

// io.on('connection', function(socket){
//
//   console.log('a user connected', socket.id);
//   // console.log(socket.id)
//
//   socket.on('disconnect', function(){
//     // console.log('user disconnected: ', socket.id);
//     room.disconnectPlayer(socket.id)
//   });
//
//   socket.on('name', function(name) {
//     // console.log("renaming: ", socket.id, name[0])
//     // var p = new Player(name, socket);
//     room.name(name, socket);
//   });
//
//   socket.on('play', function() {
//     room.ready(socket.id)
//   });
//
//
// });

server.listen(3000, function(){
  console.log('listening on *:3000');
});
