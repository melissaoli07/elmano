/*
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";


const firebaseConfig = {
  apiKey: ,
  authDomain: ,
  projectId: ,
  storageBucket: ",
  messagingSenderId: ,
  appId: ,
};


const app = initializeApp(firebaseConfig);

const db = getFirestore(app);

export { db };

-------------------------------------------------------------------------------------

CRUD

#Adicionar

import { collection, addDoc } from "firebase/firestore";
import { db } from "./firebase";

async function addData() {
  try {
    const docRef = await addDoc(collection(db, ), {
      
      
    });
    console.log("Documento adicionado com ID: ", docRef.id);
  } catch (error) {
    console.error("Erro ao adicionar documento: ", error);
  }
}

#Ler 

import { collection, getDocs } from "firebase/firestore";
import { db } from "./firebase";

async function fetchData() {
  const querySnapshot = await getDocs(collection(db, ""));
  querySnapshot.forEach((doc) => {
    console.log(`${doc.id} => `, doc.data());
  });
}

#Atualizar

import { doc, updateDoc } from "firebase/firestore";
import { db } from "./firebase";

async function updateData(docId) {
  const docRef = doc(db, "", docId);
  await updateDoc(docRef, {
    
  });
}

#Deletar

import { doc, deleteDoc } from "firebase/firestore";
import { db } from "./firebase";

async function deleteData(docId) {
  const docRef = doc(db, users", docId);
  await deleteDoc(docRef);
}



*/