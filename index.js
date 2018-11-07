require('dotenv').config();
const Discord = require("discord.js");
var rest = require('node-rest-client').Client;
const readLastLines = require('read-last-lines');
var credentials = require('./configuration.json');
var fs = require('fs');

var client = new Discord.Client();
var nodeRestClientForUse = new rest();
var neatclipClient = new rest();
var restClient = new rest();
var restClient2 = new rest();

var gKey = credentials.gKey;

var args = {
    headers: { "Client-ID": credentials.twitchauth } // request headers
};

//console.log(args);

var t1PostedOnDiscord = false;
var isT1Live = false;
var online = false;
var postedToDiscord = false;


client.on('ready', () => {
    //console.log("checking api");
    //runs whatevers in this funtion every 20 seconds
    setInterval(function(){
        restClient.get("https://www.youtube.com/ice_poseidon/live",function (data,response){
            data = String(data);
        //    console.log("HES LIVE CHECK WHAT HAPPEN NOW WITH OFFICIAL API");
        //    console.log(data);
        //if JSON response doesn't have "Live stream offline", than ice is online"
            if (data.search("Live stream offline") == -1){
                //setting online true will trigger other function
                online = true;

        //ice is offline
            }else{
                online = false;
                //postedToDiscord false means don't need to post a message to discord since offline, and won't trigger other function
                postedToDiscord = false;
            }
        });

        // 51496027 t1-s ID 62804432 is priyams 17582288 is itachipower
        //console.log("checking");
        nodeRestClientForUse.get("https://api.twitch.tv/helix/streams?user_id=51496027", args,function (data, response) {
        //   console.log(data);
        //   console.log(data['data']);
        //   console.log(data['data'].length);
            if((data['data'].length != 0) && (!isT1Live)){
                //console.log("live!");
                //console.log(data['data'][0]);
                //console.log("live");
                if (!t1PostedOnDiscord){
                    // post on discord
                    isT1Live = true;
                    var hourZULU = data['data'][0]['started_at'].substring(11,13);
                    var minutesZULU = parseInt(data['data'][0]['started_at'].substring(14,16));
                    var hourEST = (parseInt(hourZULU) - 5 + 24) % 12;
                    
                    if (minutesZULU < 10){
                        minutesZULU = '0' + minutesZULU;
                    }
                    client.channels.get("173611297387184129").send("<@173611085671170048> <@173610714433454084> T1 LIVE  https://www.twitch.tv/loltyler1 - stream started at " + hourEST + ':' + (minutesZULU));
                    t1PostedOnDiscord = true;
                }
            }else{
                if (isT1Live){
                    client.channels.get("173611297387184129").send("t1 stoped streaming");
                }
                isT1Live = false;
                // console.log("not live");
                t1PostedOnDiscord = false;
            }
        });

        if ((online) && (!postedToDiscord)){
        //    console.log("checking main googleapi");
            restClient2.get("https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=UCv9Edl_WbtbPeURPtFDo-uA&type=video&eventType=live&key=" + gKey, function(data2,response2){
                data2STRING = String(data2);
        //        console.log(data2STRING);
                if (data2.items != null){  //confirmed live, now post it on discord!
                    var currentdate = new Date(); 
                    var datetime = (currentdate.getMonth()+1)+ "/"
                                    +  currentdate.getDate()  + "/" 
                                    + currentdate.getFullYear() + " @ "  
                                    + currentdate.getHours() + ":"  
                                    + currentdate.getMinutes() + ":" 
                                    + currentdate.getSeconds();
                    client.channels.get("173611297387184129").send("<@173611085671170048> <@173610714433454084> ICE LIVE https://www.youtube.com/watch?v=" + data2.items[0].id.videoId);
                    
                    fs.writeFile("icevods.txt","https://www.youtube.com/watch?v=" + data2.items[0].id.videoId + "  " + datetime + '\n', (err) =>{
                        if (err) throw err; 
                    });
                    postedToDiscord = true;
                }else{  //confirmed not live!
                    //console.log("checked main api, offline");
                }

            });
        }

    },300000)


});


client.on("message", function(message){

    if (message.content.startsWith("--h")) {
        message.channel.send("Commands: !ice last #, !ice top hour/day/week/month/year/alltime")
    }
    if (message.content.startsWith("!ice top")){

        var args = message.content.split(/ +/g);
        var typeOfContent = args[1]; //can be new/old/top/random... of "!ice top 5 week"
        var howManyClips = args[2]; //how many clips to show
        var inHowLongDuration = args[3]; //can be hour for last hour, day..., week..., month..., year..., alltime

        var stringToSend = "";
        neatclipClient.get("https://neatclip.com/api/v1/clips.php?streamer_url=https://www.youtube.com/channel/UCv9Edl_WbtbPeURPtFDo-uA&time=" + inHowLongDuration + "&sort=" + typeOfContent, arguments, function (data, response){
        
            var size = howManyClips;
            
            if (data.length < size) size = data.length;
            for (var x = 0; x < size; x++){
                var entry = [data[x]["slugID"], data[x]["viewsAll"]];
                stringToSend = stringToSend + "https://neatclip.com/clip/" + data[x]["slugId"] + " views:" + data[x]["viewsAll"] + "\n";
            }

            message.channel.send(stringToSend);

        });
    } else if (message.content.startsWith('!ice last')){

        var numberofVods = message.content[2];
        readLastLines.read('icevods.txt',numberofVods).then((lines) => 
            message.channel.send(lines));
    }
});


client.login(credentials.discordclientlogin);