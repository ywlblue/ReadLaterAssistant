# Ask audit 2026-11-10 (dev, model=gpt-4o)

Fill each case: relevant = yes/no/partial, citation_supported = yes/no/partial.

Rubric:
- relevant: yes = answers the question; partial = on topic but incomplete; no = off topic or wrong.
- citation_supported: yes = every claim is in a cited excerpt; partial = some claims are not; no = excerpts do not support the answer.

## q06 (ask) 3102 ms, 1301+79 tokens, top_distance=0.32863926887512207

**Q:** What does Vault's transit engine do?  
**Filters:** None  
**Expected items:** ['1f44fa699fbdaa46']  
**Cites a gold item (machine):** True

**Answer:** Vault's transit secrets engine primarily encrypts data, handling cryptographic functions on data-in-transit. It also provides additional features such as signing and verifying data, generating hashes and HMACs, and acting as a source of random bytes. Vault does not store the data sent to the secrets engine, operating as encryption as a service [1].

- [1] `1f44fa699fbdaa46` https://learn.hashicorp.com/tutorials/vault/eaas-transit  
  > The transit secrets engine primary use case is to encrypt data. This relieves the burden of data encryption and decryption from the application developers and moves the burden to Vault. The transit secrets engine also provides the following features: Sign and verify data Generate hashes and HMACs of data Act as a source of random bytes Vault's transit secrets engine handles cryptographic functions on data-in-transit . Vault doesn't store the data sent to the secrets engine, so it can also be viewed as encryption as a service . Challenge Example Inc. recently made headlines for a massive data b

- relevant: Yes
- citation_supported: Yes
- notes: 

## q07 (ask) 1767 ms, 1220+118 tokens, top_distance=0.29624390602111816

**Q:** How OpenCV is being used to recognize face in Java programming.  
**Filters:** None  
**Expected items:** ['bd7e7d9395b2585e']  
**Cites a gold item (machine):** True

**Answer:** OpenCV is used in Java programming for face recognition by manually building the library as the pre-built Java bindings do not include facial recognition modules [1]. After building the library, you need to set up the environment variables and user library in Eclipse [2]. The face recognition uses algorithms like Eigenfaces, Fisherfaces, and Local Binary Patterns Histograms, with Eigenfaces being demonstrated by training the algorithm on image data and then testing with a separate image [3][4].

- [1] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > By Manish Bansal Ever since the Artificial Intelligence boom began — or the iPhone X advertisement featuring the face unlock feature hit TV screens — I’ve wanted to try this technology. However, once I started googling about it, I typically only found code examples in Python. And being a Java enthusiast for seven years, I got demotivated seeing that. Therefore, I finally decided to hunt for Java open source libraries for this. Currently, there are various Java libraries out there. But the most popular one I found was OpenCV . OpenCV is an open source computer vision library that has tons of mo
- [2] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > Hands on with OpenCV face recognition API _Photo by [Unsplash](https://unsplash.com/@rawpixel?utm_source=medium&utm_medium=referral" rel="noopener" target="_blank" title="">rawpixel on <a href="https://unsplash.com?utm_source=medium&utm_medium=referral" rel="noopener" target=" blank" title=") Now that you have built the library, you first need to set up the environment variables, as well as the user library, in Eclipse. Create a variable OPENCV_JAVA_BIN and point it to the “bin” folder generated inside your “build” directory. Create OPENCV_JAVA_LIB and point it to the “lib” folder generated in
- [3] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > first . The only issues you will encounter at this point will be related to system environment variables or user library setup. FaceDetection : you can use this to test the face detection module. It is a different module from face recognition. This is a module which gets shipped along with standard release of OpenCV. As of this writing, we can provide an image as an input to the program, and it will detect all the faces inside the image. The output image has green rectangles drawn on all the detected faces. Input image for Face Detection program Output image of face detection program FaceRecog
- [4] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > After this, you can run the face recognition program. Below are the steps performed in the program: OpenCV library is loaded as usual. The .csv file is read, and two ArrayList(s) are created . One for the matrix of images and other for their corresponding labels. Out of the 400 input images, the last entry in the list data structure is removed and saved for testing the trained model later. After that, the remaining 399 images are used for training the Eigenfaces algorithm. Once training is complete, the model is asked to predict the label of the image we removed in step 3. Output of Face Recog

- relevant: Yes
- citation_supported: Partial 
- notes: Top 1 is not strongly related which is more like a introduction about OpenCV.

## q08 (ask) 1276 ms, 1249+39 tokens, top_distance=0.3262196183204651

**Q:** What's the time complexity of inserting a node into a B+ tree?  
**Filters:** None  
**Expected items:** ['ec5068129a845350']  
**Cites a gold item (machine):** True

**Answer:** The time complexity of inserting a node into a B+ tree is Θ(logn) in the worst case.

- [1] `ec5068129a845350` https://iq.opengenus.org/b-tree-search-insert-delete-operations/  
  > In either case, we will need to repeat the removal algorithm on the parent node to remove the “split key” that previously separated these merged nodes — unless the parent is the root and we are removing the final key from the root, in which case the merged node becomes the new root (and the tree has become one level shorter than before). The figure depicts the searching of an element in a B-Tree. **The figure illustrates the insertion of an element in a B+ Tree. B+ tree grows at the root and not at the leaves.** The figure illustrates the deletion of an element from a b+ tree. Complexity Worst
- [2] `fa0d7f37d6a419ca` https://opendsa-server.cs.vt.edu/ODSA/Books/CS3/html/BTree.html  
  > siblings, and the total reduced to two nodes. Thus, the nodes are always at least two thirds full. [ 1 ] Finally, here is an example of building a B+ Tree of order five. You can compare this to the example above of building a tree of order four with the same records. Settings Saving... Server Error Resubmit Figure 12.6.7: An example of building a B+ tree of degree 5 Click here for a visualization that will let you construct and interact with a \(\mathrm{B}^+\) tree. This visualization was written by David Galles of the University of San Francisco as part of his Data Structure Visualizations pa

- relevant: Yes
- citation_supported: No
- notes: Both citations are related to B+ tree but neither answer the question directly. Maybe top 1 got truncated.

## q09 (ask) 1639 ms, 1668+72 tokens, top_distance=0.436797559261322

**Q:** Can we use a public known initial value as the key in AES-GSM encryption?  
**Filters:** None  
**Expected items:** ['62cef9f9439b4963']  
**Cites a gold item (machine):** True

**Answer:** No, the initial value (IV) should not be used as the key in AES-GCM encryption. The IV can be publicly known, but the key must remain private and confidential as it is the actual secret used to perform encryption and decryption [1][2].

- [1] `62cef9f9439b4963` https://mkyong.com/java/java-aes-encryption-and-decryption/  
  > int index = 0; while (index < hex.length()) { result.add(hex.substring(index, Math.min(index + blockSize, hex.length()))); index += blockSize; } return result.toString(); } } 2. AES encryption and decryption. The AES-GSM is the most widely used authenticated cipher. This example will encrypt and decrypt a string using 256-bit AES in Galois Counter Mode (GCM) . The AES-GCM inputs: AES Secret key (256 bits) IV – 96 bits (12 bytes) Length (in bits) of authentication tag – 128 bits (16 bytes) 2.1 In Java, we use AES/GCM/NoPadding to represent the AES-GCM algorithm. For the encrypted output, we pre
- [2] `62cef9f9439b4963` https://mkyong.com/java/java-aes-encryption-and-decryption/  
  > Key (hex)                     :603d87185bf855532f14a77a91ec7b025c004bf664e9f5c6e95613ee9577f436 Decrypted (plain text)        :Hello World AES-GCM Plain Text : Hello World AES-GCM, Welcome to Cryptography! Terminal ------ AES GCM Encryption ------ Input (plain text)            :Hello World AES-GCM, Welcome to Cryptography! Key (hex)                     :ddc24663d104e1c2f81f11aef98156503dafdc435f81e3ac3d705015ebab095c IV  (hex)                     :b05d6aedf023f73b9e1e2d11 Encrypted (hex)               :b05d6aedf023f73b9e1e2d11f6f5137d971aea8c5cdd5b045e0960eb4408e0ee4635cccc2dfeec2c13a89bd400f6

- relevant: Yes
- citation_supported: No
- notes: 

## q10 (ask) 1898 ms, 1536+101 tokens, top_distance=0.590122401714325

**Q:** I want to integrate Twillo into my system and receive recepient reaction, how to track it via webhook?  
**Filters:** None  
**Expected items:** ['87d874a621649a2d']  
**Cites a gold item (machine):** True

**Answer:** To track recipient reactions using Twilio, you can utilize engagement events provided by SendGrid's Event Webhook. These events include interactions such as opens, clicks, spam reports, unsubscribes, group unsubscribes, and group resubscribes [4]. You should ensure 'Subscription Tracking' and 'Open Tracking' are turned on to effectively monitor these interactions [3][5].

- [3] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > Positive Feedback Negative Feedback Recipient clicked on the Opt Out of All Emails link. To track subscriptions, turn on Subscription Tracking . Example webhook response for unsubscribe events example-webhook-response-for-unsubscribe-events page anchor Copy code block 1 [ 2 { 3 "email" : "alex@example.com" , 4 "timestamp" : 1513299569 , 5 "event" : "unsubscribe" , 6 "category" : "cat facts" , 7 "sg_event_id" : "zz_BjPgU_5pS-J8vlfB1sg==" , 8 "sg_message_id" : "14c5d75ce93.dfd.64b469.filter0001.16648.5515E0B88.0" 9 } 10 ] Group resubscribe events group-resubscribe-events page anchor Positive Fee
- [4] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > Positive Feedback Negative Feedback When Twilio SendGrid and email service providers process email messages, these messages generate events that Twilio logs. Twilio tracks three types of events: delivery, engagement, and account. Delivery events that indicate the status of email delivery to the recipient. Engagement events that indicate how the recipient is interacting with the email. Account change events that indicate changes and impacts to your account. Delivery events delivery-events page anchor Positive Feedback Negative Feedback Delivery events cover messages that were bounced , delivere
- [5] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > , 5 "ip" : "255.255.255.255" , 6 "useragent" : "Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 Safari/9537.53" , 7 "event" : "click" , 8 "email" : "email@example.com" , 9 "timestamp" : 1249948800 , 10 "url" : "http://example.com/blog/news.html" , 11 "url_offset" : { 12 "index" : 0 , 13 "type" : "html" 14 }, 15 "unique_arg_key" : "unique_arg_value" , 16 "category" : [ "category1" , "category2" ], 17 "newsletter" : { 18 "newsletter_user_list_id" : "10557865" , 19 "newsletter_id" : "1943530" , 20 "newsletter_send_id" : "2

- relevant: Yes
- citation_supported: 3 & 4 are more related.
- notes: 

## q11 (filter) 1758 ms, 1235+72 tokens, top_distance=0.3851897716522217

**Q:** How to identify a problem that can be solved using Dynamic Programming?  
**Filters:** {'domain': 'www.geeksforgeeks.org'}  
**Expected items:** ['783c3656a3bbcbe2']  
**Cites a gold item (machine):** True

**Answer:** A problem that can be solved using Dynamic Programming typically has a recursive solution with repeated calls for the same inputs. The key idea is to optimize by storing results of subproblems to avoid re-computation, thereby reducing time complexities from exponential to polynomial [1].

- [1] `783c3656a3bbcbe2` https://www.geeksforgeeks.org/dynamic-programming/  
  > Courses Sale Tutorials Interview Prep DSA Tutorial Interview Questions Quizzes Must Do Advanced DSA System Design Aptitude Puzzles Interview Corner DSA Python Dynamic Programming or DP Last Updated : 17 Oct, 2026 Dynamic Programming is an algorithmic technique with the following properties. It is mainly an optimization over plain recursion. Wherever we see a recursive solution that has repeated calls for the same inputs, we can optimize it using Dynamic Programming. The idea is to simply store the results of subproblems so that we do not have to re-compute them when needed later. This simple o

- relevant: Yes
- citation_supported: Yes
- notes: 

## q14 (filter) 2131 ms, 1193+76 tokens, top_distance=0.407556414604187

**Q:** That article I saved on Oct 12 about scaling systems, how do you get horizontal scalability?  
**Filters:** {'since': 20261012, 'until': 20261012}  
**Expected items:** ['4338a0684b4cd642']  
**Cites a gold item (machine):** True

**Answer:** Horizontal scalability is achieved by adding more machines to increase capacity and using load balancing to distribute requests across the resources. Load balancing helps ensure that the system's capacity increases linearly with added hardware, as it spreads requests based on certain metrics like round-robin or machine capacity [1][2].

- [1] `4338a0684b4cd642` https://lethain.com/introduction-to-architecting-systems-for-scale/  
  > If you had three and you add another, your capacity would increase by 33%. Let’s call this horizontal scalability . On the failure side, an ideal system isn’t disrupted by the loss of a server. Losing a server should simply decrease system capacity by the same amount it increased overall capacity when it was added. Let’s call this redundancy . Both horizontal scalability and redundancy are usually achieved via load balancing. (This article won’t address vertical scalability , as it is usually an undesirable property for a large system, as there is inevitably a point where it becomes cheaper to
- [2] `4338a0684b4cd642` https://lethain.com/introduction-to-architecting-systems-for-scale/  
  > Few computer science or software development programs attempt to teach the building blocks of scalable systems. Instead, system architecture is usually picked up on the job by working through the pain of a growing product or by working with engineers who have already learned through that suffering process. In this post I’ll attempt to document some of the scalability architecture lessons I’ve learned while working on systems at Yahoo! and Digg . I’ve attempted to maintain a color convention for diagrams: green is an external request from an external client (an HTTP request from a browser, etc)

- relevant: Yes
- citation_supported: Partial
- notes: 1 is strongly related but 2 not

## q01 (vague) 1170 ms, 1184+38 tokens, top_distance=0.49313896894454956

**Q:** There's an article about a popular k-drama. What's the name of the k-drama?  
**Filters:** None  
**Expected items:** ['af4bdf3132b2fdee']  
**Cites a gold item (machine):** True

**Answer:** The name of the K-drama is 'Take Charge of My Heart.'

- [1] `af4bdf3132b2fdee` https://time.com/article/2026/10/01/take-charge-of-my-heart-ending-explained  
  > Korean dramas are famously chaste compared to Western TV series. Though there are some exceptions , most K-dramas shy away from featuring even passionate kissing, let alone full-on sex scenes. But Take Charge of My Heart , Netflix’s latest Korean-language romance, adds a jolt, making  “skinship,” or the physical intimacy between two people, a central part of its premise. In the supernatural series, TV scriptwriter Na Bo-bae ( When the Phone Rings ’ Chae Soo-bin) has electrical currents coursing through her body, making it so she will zap anyone she touches with bare hands. Because of the condi
- [2] `af4bdf3132b2fdee` https://time.com/article/2026/10/01/take-charge-of-my-heart-ending-explained  
  > Meanwhile, chaebol heir Baek Ho-rang ( Trigger ’s Kim Young-kwang) has an artificial heart that is failing. When Ho-rang and Bo-bae happen to be in the hospital at the same time, Ho-rang’s doctor discovers that physical proximity to Bo-bae charges Ho-rang’s artificial heart. Even more shocking to Bo-bae, she can touch Ho-rang without anything happening to him. As Ho-rang waits for a surgery for a new artificial heart in three months, the two strike a deal: Bo-bae will move into Ho-rang’s massive house, and act as his portable charger, and Ho-rang will go out on dates with Bo-bae as research fo
- [5] `af4bdf3132b2fdee` https://time.com/article/2026/10/01/take-charge-of-my-heart-ending-explained  
  > Meanwhile, Bo-bae uses her electric powers to escape from the temple Do-yoon’s hired goons have locked her in. She and Jae-ho rush to the party and arrive shortly after Ho-rang has collapsed. A desperate Bo-bae gives Ho-rang CPR, and sends a massive electrical current into his body. Ho-rang’s heart starts beating again, but Bo-bae collapses in the effort. When she wakes up again, Ho-rang’s doctor tells Bo-bae that she can’t touch Ho-rang again without endangering his life. He had surgery to get a new artificial heart, and Bo-bae’s electrical touch could stop it. Advertisement Chae Soo-bin as N

- relevant: Yes
- citation_supported: Yes
- notes: I just want to know the name about that drama but the citation seems to overwhelm maybe because it mentions K-drama in the intercept.

## q29 (vague) 1440 ms, 1154+54 tokens, top_distance=0.5753862261772156

**Q:** What's the article about the king who has lots of wives?  
**Filters:** None  
**Expected items:** ['e8cd234919c4f656']  
**Cites a gold item (machine):** True

**Answer:** The article is about Henry VIII, who is known for his six marriages and tumultuous reign, which included breaking with the Catholic Church and reshaping the religious and political landscape of England [1].

- [1] `e8cd234919c4f656` https://academytravel.com.au/blog/behind-the-throne-henry-viii-england-key-sites  
  > Behind the Throne History 18 Dec Written by Dr Lauren Mackay Getting to know Henry VIII Henry VIII is one of the most famous monarchs - in his 38-year reign he married six times, broke with the Catholic Church, and ruled during one of the most politically tumultuous periods in England’s history. When the 18-year-old Henry VIII ascended the throne of England in 1509, he was determined to epitomise the age as a Golden Renaissance Prince. His reign marked the shift from the medieval period to the early modern world, and the handsome, educated, and athletic Henry was devoted to new learning of the

- relevant: Yes
- citation_supported: Yes
- notes: 

## q23 (find) 2003 ms, 1275+122 tokens, top_distance=0.3442257046699524

**Q:** What's the difference of UDP and TCP, and their usage?  
**Filters:** None  
**Expected items:** ['5c35d650e1d44697', 'ef75458f6e296e61', '6a4e30c82368e2a2']  
**Cites a gold item (machine):** True

**Answer:** UDP is a simple, connection-less protocol that does not guarantee data delivery, order, or uniqueness, making it suitable for applications where speed is critical and errors can be tolerated, such as streaming media or certain online games [1][5]. TCP, on the other hand, provides a connection-oriented service with built-in reliability, ensuring that data packets are delivered in the correct order without loss, making it suitable for applications requiring high reliability like web browsing and email [2][3].

- [1] `5c35d650e1d44697` https://www.cs.dartmouth.edu/~campbell/cs60/socketprogramming.html  
  > User Datagram Protocol (UDP) UDP is a simple transport-layer protocol. The application writes a message to a UDP socket, which is then encapsulated in a UDP datagram, which is further encapsulated in an IP datagram, which is sent to the destination. There is no guarantee that a UDP will reach the destination, that the order of the datagrams will be preserved across the network or that datagrams arrive only once. The problem of UDP is its lack of reliability: if a datagram reaches its final destination but the checksum detects an error, or if the datagram is dropped in the network, it is not au
- [2] `5c35d650e1d44697` https://www.cs.dartmouth.edu/~campbell/cs60/socketprogramming.html  
  > TCP provides a connection oriented service , since it is based on connections between clients and servers. TCP provides reliability. When a TCP client send data to the server, it requires an acknowledgement in return. If an acknowledgement is not received, TCP automatically retransmit the data and waits for a longer period of time. We have mentioned that UDP datagrams are characterized by a length. TCP is instead a byte-stream protocol, without any boundaries at all. TCP is described in RFC 793, RFC 1323, RFC 2581 and RFC 3390. Socket addresses IPv4 socket address structure is named sockaddr_i
- [3] `ef75458f6e296e61` https://gafferongames.com/post/reliability_ordering_and_congestion_avoidance_over_udp/  
  > The problem with TCP is that it abstracts data delivery as a reliable ordered stream. Because of this, if a packet is lost, TCP has to stop and wait for that packet to be resent. This interrupts the steady stream of packets because more recent packets must wait in a queue until the resent packet arrives, so packets are received in the same order they were sent. What we need is a different type of reliability. Instead of having all data treated as a reliable ordered stream, we want to send packets at a steady rate and get notified when packets are received by the other computer. This allows tim
- [5] `5c35d650e1d44697` https://www.cs.dartmouth.edu/~campbell/cs60/socketprogramming.html  
  > <unistd.h> int close(int sockfd); UDP Socket API There are some fundamental differences between TCP and UDP sockets. UDP is a connection-less, unreliable, datagram protocol (TCP is instead connection-oriented, reliable and stream based). There are some instances when it makes to use UDP instead of TCP. Some popular applications built around UDP are DNS, NFS, SNMP and for example, some Skype services and streaming media. Figure 4 shows the the interaction between a UDP client and server. First of all, the client does not establish a connection with the server. Instead, the client just sends a d

- relevant: Yes
- citation_supported: Yes
- notes: Yes

---

## Re-check (11/10, final values are in the .jsonl)

The first version of this sheet cut each excerpt at 600 characters, but the model saw the full chunk (~1000 chars).
Re-checked q07, q08, q09, q10 and q14 against the full excerpts: the missing evidence was in the cut part.
Script fixed (`run_ask_audit.py` now prints full excerpts).

Final: relevant 10/10, citation supported 10/10. Mean latency 1819 ms (max 3102 ms), est. cost $0.0402 for 10 asks (gpt-4o).

Separate finding, not part of the support score: citation precision. q01 cites 3 excerpts for a one-line answer; q07 [1] is weak for the main question.
